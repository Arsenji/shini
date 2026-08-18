import AppKit
import Foundation
import ImageIO
import UniformTypeIdentifiers

func luminance(_ r: UInt8, _ g: UInt8, _ b: UInt8) -> Int {
    (Int(r) * 299 + Int(g) * 587 + Int(b) * 114) / 1000
}

func isBackground(_ r: UInt8, _ g: UInt8, _ b: UInt8) -> Bool {
    let rr = Int(r), gg = Int(g), bb = Int(b)
    let sat = max(rr, max(gg, bb)) - min(rr, min(gg, bb))
    return luminance(r, g, b) >= 228 && sat <= 28
}

func process(src: URL, dest: URL) throws {
    guard let srcImage = NSImage(contentsOf: src),
          let cg = srcImage.cgImage(forProposedRect: nil, context: nil, hints: nil)
    else {
        throw NSError(domain: "cut-tire", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot read \(src.lastPathComponent)"])
    }

    let width = cg.width
    let height = cg.height
    let count = width * height
    let bytesPerRow = width * 4
    let ptr = UnsafeMutablePointer<UInt8>.allocate(capacity: count * 4)
    ptr.initialize(repeating: 0, count: count * 4)
    defer { ptr.deallocate() }

    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(
        data: ptr,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: bytesPerRow,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
        throw NSError(domain: "cut-tire", code: 2, userInfo: [NSLocalizedDescriptionKey: "No context"])
    }
    ctx.draw(cg, in: CGRect(x: 0, y: 0, width: width, height: height))

    var visited = [UInt8](repeating: 0, count: count)
    var queue = [Int]()
    queue.reserveCapacity(width * 4)

    func pushIfBg(_ x: Int, _ y: Int) {
        if x < 0 || y < 0 || x >= width || y >= height { return }
        let i = y * width + x
        if visited[i] == 1 { return }
        let p = i * 4
        if isBackground(ptr[p], ptr[p + 1], ptr[p + 2]) {
            visited[i] = 1
            queue.append(i)
        }
    }

    for x in 0..<width {
        pushIfBg(x, 0)
        pushIfBg(x, height - 1)
    }
    for y in 0..<height {
        pushIfBg(0, y)
        pushIfBg(width - 1, y)
    }

    var qHead = 0
    while qHead < queue.count {
        let i = queue[qHead]
        qHead += 1
        let x = i % width
        let y = i / width
        pushIfBg(x + 1, y)
        pushIfBg(x - 1, y)
        pushIfBg(x, y + 1)
        pushIfBg(x, y - 1)
    }

    // Eat the anti-aliased white halo around the tire.
    var dilated = visited
    for _ in 0..<3 {
        var next = dilated
        for y in 0..<height {
            for x in 0..<width {
                let i = y * width + x
                if dilated[i] == 1 { continue }
                let p = i * 4
                let lum = luminance(ptr[p], ptr[p + 1], ptr[p + 2])
                if lum < 170 { continue }
                var near = false
                for dy in -1...1 {
                    for dx in -1...1 {
                        if dx == 0 && dy == 0 { continue }
                        let nx = x + dx, ny = y + dy
                        if nx < 0 || ny < 0 || nx >= width || ny >= height { continue }
                        if dilated[ny * width + nx] == 1 { near = true }
                    }
                }
                if near { next[i] = 1 }
            }
        }
        dilated = next
    }

    for i in 0..<count where dilated[i] == 1 {
        let p = i * 4
        ptr[p] = 0
        ptr[p + 1] = 0
        ptr[p + 2] = 0
        ptr[p + 3] = 0
    }

    var minX = width, minY = height, maxX = 0, maxY = 0
    for y in 0..<height {
        for x in 0..<width {
            if ptr[(y * width + x) * 4 + 3] > 12 {
                if x < minX { minX = x }
                if y < minY { minY = y }
                if x > maxX { maxX = x }
                if y > maxY { maxY = y }
            }
        }
    }
    if maxX <= minX || maxY <= minY {
        throw NSError(domain: "cut-tire", code: 3, userInfo: [NSLocalizedDescriptionKey: "Empty after cut \(src.lastPathComponent)"])
    }

    let pad = max(4, Int(Double(max(width, height)) * 0.02))
    minX = max(0, minX - pad)
    minY = max(0, minY - pad)
    maxX = min(width - 1, maxX + pad)
    maxY = min(height - 1, maxY + pad)
    let cropW = maxX - minX + 1
    let cropH = maxY - minY + 1
    // CGImage cropping uses top-left origin; our buffer is bottom-left.
    let cropY = height - maxY - 1

    guard let full = ctx.makeImage(),
          let cropped = full.cropping(to: CGRect(x: minX, y: cropY, width: cropW, height: cropH)),
          let destination = CGImageDestinationCreateWithURL(dest as CFURL, UTType.png.identifier as CFString, 1, nil)
    else {
        throw NSError(domain: "cut-tire", code: 4, userInfo: [NSLocalizedDescriptionKey: "Cannot write \(dest.lastPathComponent)"])
    }
    CGImageDestinationAddImage(destination, cropped, nil)
    if !CGImageDestinationFinalize(destination) {
        throw NSError(domain: "cut-tire", code: 5, userInfo: [NSLocalizedDescriptionKey: "Finalize failed \(src.lastPathComponent)"])
    }
}

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let files = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
    .filter { ["webp", "jpg", "jpeg", "png"].contains($0.pathExtension.lowercased()) }
    .filter { !$0.lastPathComponent.hasPrefix(".") }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }

for file in files {
    let stem = file.deletingPathExtension().lastPathComponent
    let out = dir.appendingPathComponent(stem + ".png")
    let tmp = dir.appendingPathComponent("." + stem + ".tmp.png")
    try process(src: file, dest: tmp)
    if file.pathExtension.lowercased() == "png" {
        try FileManager.default.removeItem(at: file)
    }
    if FileManager.default.fileExists(atPath: out.path) {
        try FileManager.default.removeItem(at: out)
    }
    try FileManager.default.moveItem(at: tmp, to: out)
    if file.pathExtension.lowercased() != "png", FileManager.default.fileExists(atPath: file.path) {
        try FileManager.default.removeItem(at: file)
    }
    print("ok \(file.lastPathComponent) -> \(out.lastPathComponent)")
}
