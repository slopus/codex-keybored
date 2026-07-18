#!/usr/bin/env swift

import AppKit
import CoreGraphics
import CoreText
import Foundation

struct Point2D: Codable {
    let x: Double
    let y: Double
}

struct Bounds: Codable {
    let minX: Double
    let minY: Double
    let maxX: Double
    let maxY: Double

    var width: Double { maxX - minX }
    var height: Double { maxY - minY }
}

struct TextArtwork: Codable {
    let text: String
    let fontPostScriptName: String
    let nominalFontSize: Double
    let centerX: Double
    let centerY: Double
    let bounds: Bounds
    let contours: [[Point2D]]
}

struct PackageGeometry: Codable {
    let revision: String
    let units: String
    let part: String
    let machiningItem: String
    let view: String
    let rearDirection: String
    let partDiameter: Double
    let grooveCenterDiameter: Double
    let grooveWidth: Double
    let holePitchRadius: Double
    let holeDiameter: Double
    let counterboreDiameter: Double
    let artwork: [TextArtwork]
}

private func fontFromFile(_ path: String, size: CGFloat) throws -> CTFont {
    let url = URL(fileURLWithPath: path) as CFURL
    guard let descriptors = CTFontManagerCreateFontDescriptorsFromURL(url) as? [CTFontDescriptor],
          let descriptor = descriptors.first else {
        throw NSError(domain: "LaserArtwork", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot load font at \(path)"])
    }
    return CTFontCreateWithFontDescriptor(descriptor, size, nil)
}

private func nearlyEqual(_ a: Point2D, _ b: Point2D, epsilon: Double = 1e-8) -> Bool {
    abs(a.x - b.x) < epsilon && abs(a.y - b.y) < epsilon
}

private func flatten(path: CGPath, offset: CGPoint, subdivisions: Int = 16) -> [[Point2D]] {
    var contours: [[Point2D]] = []
    var contour: [Point2D] = []
    var current = Point2D(x: 0, y: 0)
    var start = Point2D(x: 0, y: 0)

    func point(_ p: CGPoint) -> Point2D {
        Point2D(x: Double(p.x + offset.x), y: Double(p.y + offset.y))
    }

    func finishContour() {
        guard contour.count >= 3 else {
            contour.removeAll(keepingCapacity: true)
            return
        }
        if nearlyEqual(contour.last!, contour.first!) {
            contour.removeLast()
        }
        if contour.count >= 3 {
            contours.append(contour)
        }
        contour.removeAll(keepingCapacity: true)
    }

    path.applyWithBlock { elementPointer in
        let element = elementPointer.pointee
        switch element.type {
        case .moveToPoint:
            finishContour()
            current = point(element.points[0])
            start = current
            contour.append(current)
        case .addLineToPoint:
            current = point(element.points[0])
            contour.append(current)
        case .addQuadCurveToPoint:
            let p0 = current
            let p1 = point(element.points[0])
            let p2 = point(element.points[1])
            for index in 1...subdivisions {
                let t = Double(index) / Double(subdivisions)
                let u = 1.0 - t
                contour.append(Point2D(
                    x: u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
                    y: u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y
                ))
            }
            current = p2
        case .addCurveToPoint:
            let p0 = current
            let p1 = point(element.points[0])
            let p2 = point(element.points[1])
            let p3 = point(element.points[2])
            for index in 1...subdivisions {
                let t = Double(index) / Double(subdivisions)
                let u = 1.0 - t
                contour.append(Point2D(
                    x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
                    y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y
                ))
            }
            current = p3
        case .closeSubpath:
            current = start
            finishContour()
        @unknown default:
            break
        }
    }
    finishContour()
    return contours
}

private func bounds(of contours: [[Point2D]]) -> Bounds {
    let points = contours.flatMap { $0 }
    return Bounds(
        minX: points.map(\.x).min()!,
        minY: points.map(\.y).min()!,
        maxX: points.map(\.x).max()!,
        maxY: points.map(\.y).max()!
    )
}

private func createArtwork(
    text: String,
    fontPath: String,
    nominalFontSize: Double,
    centerY: Double
) throws -> TextArtwork {
    let font = try fontFromFile(fontPath, size: 100)
    let attributes: [NSAttributedString.Key: Any] = [
        NSAttributedString.Key(kCTFontAttributeName as String): font
    ]
    let attributed = NSAttributedString(string: text, attributes: attributes)
    let line = CTLineCreateWithAttributedString(attributed)
    let runs = CTLineGetGlyphRuns(line) as NSArray
    var rawContours: [[Point2D]] = []

    for object in runs {
        let run = object as! CTRun
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRange(location: 0, length: 0), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: 0), &positions)
        for index in 0..<count {
            if let glyphPath = CTFontCreatePathForGlyph(font, glyphs[index], nil) {
                rawContours.append(contentsOf: flatten(path: glyphPath, offset: positions[index]))
            }
        }
    }

    let rawBounds = bounds(of: rawContours)
    // Match CadQuery/OpenCascade text-size semantics used by the STEP source:
    // 4.2 and 2.1 are nominal font/em sizes, not the visible cap heights.
    let scale = nominalFontSize / 100.0
    let rawCenterX = (rawBounds.minX + rawBounds.maxX) / 2
    let rawCenterY = (rawBounds.minY + rawBounds.maxY) / 2
    let transformed = rawContours.map { contour in
        contour.map { point in
            Point2D(
                x: (point.x - rawCenterX) * scale,
                y: (point.y - rawCenterY) * scale + centerY
            )
        }
    }
    let finalBounds = bounds(of: transformed)
    return TextArtwork(
        text: text,
        fontPostScriptName: CTFontCopyPostScriptName(font) as String,
        nominalFontSize: nominalFontSize,
        centerX: 0,
        centerY: centerY,
        bounds: finalBounds,
        contours: transformed
    )
}

private struct Layer {
    let name: String
    let color: Int
}

private final class DXFWriter {
    private var lines: [String] = []

    private func pair(_ code: Int, _ value: String) {
        lines.append(String(code))
        lines.append(value)
    }

    func begin(layers: [Layer]) {
        pair(0, "SECTION")
        pair(2, "HEADER")
        pair(9, "$ACADVER")
        pair(1, "AC1024")
        pair(9, "$INSUNITS")
        pair(70, "4")
        pair(9, "$MEASUREMENT")
        pair(70, "1")
        pair(0, "ENDSEC")

        pair(0, "SECTION")
        pair(2, "TABLES")
        pair(0, "TABLE")
        pair(2, "LAYER")
        pair(70, String(layers.count))
        for layer in layers {
            pair(0, "LAYER")
            pair(100, "AcDbSymbolTableRecord")
            pair(100, "AcDbLayerTableRecord")
            pair(2, layer.name)
            pair(70, "0")
            pair(62, String(layer.color))
            pair(6, "CONTINUOUS")
        }
        pair(0, "ENDTAB")
        pair(0, "ENDSEC")

        pair(0, "SECTION")
        pair(2, "ENTITIES")
    }

    func polyline(_ points: [Point2D], layer: String) {
        guard points.count >= 3 else { return }
        pair(0, "LWPOLYLINE")
        pair(100, "AcDbEntity")
        pair(8, layer)
        pair(100, "AcDbPolyline")
        pair(90, String(points.count))
        pair(70, "1")
        for point in points {
            pair(10, String(format: "%.6f", point.x))
            pair(20, String(format: "%.6f", point.y))
        }
    }

    func circle(center: Point2D, radius: Double, layer: String) {
        pair(0, "CIRCLE")
        pair(100, "AcDbEntity")
        pair(8, layer)
        pair(100, "AcDbCircle")
        pair(10, String(format: "%.6f", center.x))
        pair(20, String(format: "%.6f", center.y))
        pair(30, "0.0")
        pair(40, String(format: "%.6f", radius))
    }

    func line(from: Point2D, to: Point2D, layer: String) {
        pair(0, "LINE")
        pair(100, "AcDbEntity")
        pair(8, layer)
        pair(100, "AcDbLine")
        pair(10, String(format: "%.6f", from.x))
        pair(20, String(format: "%.6f", from.y))
        pair(30, "0.0")
        pair(11, String(format: "%.6f", to.x))
        pair(21, String(format: "%.6f", to.y))
        pair(31, "0.0")
    }

    func finish() -> String {
        pair(0, "ENDSEC")
        pair(0, "EOF")
        return lines.joined(separator: "\n") + "\n"
    }
}

private func writeDXF(
    url: URL,
    artwork: [TextArtwork],
    includePlacementReference: Bool
) throws {
    let laserLayer = Layer(name: "LASER_MARK", color: 1)
    var layers = [laserLayer]
    if includePlacementReference {
        layers += [
            Layer(name: "PART_OUTLINE_REFERENCE_DO_NOT_MARK", color: 8),
            Layer(name: "GROOVE_REFERENCE_DO_NOT_MARK", color: 9),
            Layer(name: "HOLES_REFERENCE_DO_NOT_MARK", color: 4),
            Layer(name: "REAR_DATUM_REFERENCE_DO_NOT_MARK", color: 3),
        ]
    }
    let writer = DXFWriter()
    writer.begin(layers: layers)
    for item in artwork {
        for contour in item.contours {
            writer.polyline(contour, layer: "LASER_MARK")
        }
    }

    if includePlacementReference {
        writer.circle(center: Point2D(x: 0, y: 0), radius: 47.0, layer: "PART_OUTLINE_REFERENCE_DO_NOT_MARK")
        writer.circle(center: Point2D(x: 0, y: 0), radius: 35.55, layer: "GROOVE_REFERENCE_DO_NOT_MARK")
        writer.circle(center: Point2D(x: 0, y: 0), radius: 31.95, layer: "GROOVE_REFERENCE_DO_NOT_MARK")
        let holeCenters = [
            Point2D(x: -41, y: 0), Point2D(x: 41, y: 0),
            Point2D(x: 0, y: -41), Point2D(x: 0, y: 41),
        ]
        for center in holeCenters {
            writer.circle(center: center, radius: 1.4, layer: "HOLES_REFERENCE_DO_NOT_MARK")
            writer.circle(center: center, radius: 2.5, layer: "HOLES_REFERENCE_DO_NOT_MARK")
        }
        writer.line(from: Point2D(x: 0, y: 47), to: Point2D(x: 0, y: 53), layer: "REAR_DATUM_REFERENCE_DO_NOT_MARK")
        writer.line(from: Point2D(x: 0, y: 53), to: Point2D(x: -2.2, y: 49.8), layer: "REAR_DATUM_REFERENCE_DO_NOT_MARK")
        writer.line(from: Point2D(x: 0, y: 53), to: Point2D(x: 2.2, y: 49.8), layer: "REAR_DATUM_REFERENCE_DO_NOT_MARK")
    }
    try writer.finish().write(to: url, atomically: true, encoding: .utf8)
}

private func svgPath(_ contours: [[Point2D]]) -> String {
    contours.map { contour in
        guard let first = contour.first else { return "" }
        let rest = contour.dropFirst().map { point in
            "L \(String(format: "%.5f", point.x)) \(String(format: "%.5f", point.y))"
        }.joined(separator: " ")
        return "M \(String(format: "%.5f", first.x)) \(String(format: "%.5f", first.y)) \(rest) Z"
    }.joined(separator: " ")
}

private func writeSVG(url: URL, artwork: [TextArtwork]) throws {
    let allContours = artwork.flatMap(\.contours)
    let markPath = svgPath(allContours)
    let holes = ["-41,0", "41,0", "0,-41", "0,41"].map { pair -> String in
        let values = pair.split(separator: ",")
        return "<circle cx=\"\(values[0])\" cy=\"\(values[1])\" r=\"2.5\" fill=\"#0b0d0a\" stroke=\"#747970\" stroke-width=\"0.35\"/>"
    }.joined(separator: "\n")
    let svg = """
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="-56 -56 112 112" width="1120" height="1120">
      <rect x="-56" y="-56" width="112" height="112" fill="#f4f6ef"/>
      <g transform="scale(1,-1)">
        <circle cx="0" cy="0" r="47" fill="#11130f" stroke="#050604" stroke-width="0.55"/>
        <circle cx="0" cy="0" r="35.55" fill="none" stroke="#555a52" stroke-width="0.30"/>
        <circle cx="0" cy="0" r="31.95" fill="none" stroke="#555a52" stroke-width="0.30"/>
        \(holes)
        <path d="\(markPath)" fill="#d9ddd4" fill-rule="evenodd"/>
        <path d="M 0 47 L 0 53 M 0 53 L -2.2 49.8 M 0 53 L 2.2 49.8" fill="none" stroke="#a7d528" stroke-width="0.55"/>
      </g>
      <text x="0" y="-53.5" text-anchor="middle" font-family="Arial, sans-serif" font-size="2.1" font-weight="700" fill="#11130f">REAR / THICK EDGE / USB SIDE (+Y)</text>
    </svg>
    """
    try svg.write(to: url, atomically: true, encoding: .utf8)
}

let outputPath = CommandLine.arguments.dropFirst().first ?? "cnc/vendor_response/2026-07-18_JLCCNC_laser_marking"
let outputURL = URL(fileURLWithPath: outputPath, isDirectory: true)
try FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)

let mainArtwork = try createArtwork(
    text: "CODEX KEYBORED",
    fontPath: "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    nominalFontSize: 4.2,
    centerY: 4.0
)
let strapArtwork = try createArtwork(
    text: "ABSOLUTELY VIBE-CODED",
    fontPath: "/System/Library/Fonts/Supplemental/Arial.ttf",
    nominalFontSize: 2.1,
    centerY: -4.0
)
let artwork = [mainArtwork, strapArtwork]

try writeDXF(
    url: outputURL.appendingPathComponent("CM2-002_LASER_ARTWORK_ONLY_RevB.dxf"),
    artwork: artwork,
    includePlacementReference: false
)
try writeDXF(
    url: outputURL.appendingPathComponent("CM2-002_LASER_PLACEMENT_REFERENCE_RevB.dxf"),
    artwork: artwork,
    includePlacementReference: true
)
try writeSVG(
    url: outputURL.appendingPathComponent("CM2-002_LASER_PLACEMENT_PREVIEW_RevB.svg"),
    artwork: artwork
)

let geometry = PackageGeometry(
    revision: "B",
    units: "mm",
    part: "CM2-002 bottom weight",
    machiningItem: "CNC2607185001881-3086316A",
    view: "UNDERSIDE / DESK-FACING SURFACE, looking directly at the marking face",
    rearDirection: "+Y = rear / thick edge / USB side",
    partDiameter: 94.0,
    grooveCenterDiameter: 67.5,
    grooveWidth: 3.6,
    holePitchRadius: 41.0,
    holeDiameter: 2.8,
    counterboreDiameter: 5.0,
    artwork: artwork
)
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
try encoder.encode(geometry).write(to: outputURL.appendingPathComponent("CM2-002_LASER_GEOMETRY_RevB.json"))

print("Generated JLCCNC laser-marking response package in \(outputURL.path)")
for item in artwork {
    print(String(format: "%@: %.3f x %.3f mm outline bounds, nominal font size %.3f mm, center (0, %.3f), %d closed contours", item.text, item.bounds.width, item.bounds.height, item.nominalFontSize, item.centerY, item.contours.count))
}
