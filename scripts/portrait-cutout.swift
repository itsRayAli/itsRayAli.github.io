// Lift the foreground subject from a photo using Apple's Vision framework
// and write it as a PNG with a transparent background.
import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: lift <in> <out.png>"); exit(1) }
let input = URL(fileURLWithPath: args[1]), output = URL(fileURLWithPath: args[2])

guard let src = CGImageSourceCreateWithURL(input as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("cannot read"); exit(1) }

let request = VNGenerateForegroundInstanceMaskRequest()
let handler = VNImageRequestHandler(cgImage: cg)
try handler.perform([request])
guard let result = request.results?.first else { print("no subject found"); exit(2) }
print("instances:", result.allInstances.count)

// Full-resolution soft mask, applied to the original pixels.
let masked = try result.generateMaskedImage(ofInstances: result.allInstances, from: handler, croppedToInstancesExtent: false)
let ci = CIImage(cvPixelBuffer: masked)
let ctx = CIContext()
guard let outCG = ctx.createCGImage(ci, from: ci.extent),
      let dest = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil) else { exit(3) }
CGImageDestinationAddImage(dest, outCG, nil)
CGImageDestinationFinalize(dest)
print("wrote", output.path, outCG.width, "x", outCG.height)
