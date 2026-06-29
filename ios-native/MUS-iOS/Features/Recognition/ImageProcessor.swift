import UIKit
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins

/// 可選影像預處理：預設不做自動裁切與亮度/對比調整
struct ImageProcessor {
    struct Options {
        var autoCrop: Bool = false
        var brightnessAdjust: Float = 0
        var contrastAdjust: Float = 1
    }

    static func process(_ image: UIImage, options: Options = Options()) async -> UIImage {
        var result = image

        if options.autoCrop, let cropped = await autoCrop(result) {
            result = cropped
        }

        if options.brightnessAdjust != 0 || options.contrastAdjust != 1 {
            if let adjusted = adjustBrightnessContrast(
                result,
                brightness: options.brightnessAdjust,
                contrast: options.contrastAdjust
            ) {
                result = adjusted
            }
        }

        return result
    }

    // MARK: - Vision 矩形裁切

    private static func autoCrop(_ image: UIImage) async -> UIImage? {
        guard let cgImage = image.cgImage else { return nil }

        return await withCheckedContinuation { continuation in
            let request = VNDetectRectanglesRequest { request, error in
                guard error == nil,
                      let results = request.results as? [VNRectangleObservation],
                      let rect = results.first else {
                    continuation.resume(returning: nil)
                    return
                }
                let cropped = crop(cgImage, to: rect,
                                   imageSize: CGSize(width: cgImage.width, height: cgImage.height))
                continuation.resume(returning: cropped.map { UIImage(cgImage: $0, scale: image.scale, orientation: image.imageOrientation) })
            }
            request.minimumConfidence = 0.6
            request.minimumAspectRatio = 0.3

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            try? handler.perform([request])
        }
    }

    private static func crop(_ cgImage: CGImage, to observation: VNRectangleObservation,
                               imageSize: CGSize) -> CGImage? {
        let w = imageSize.width
        let h = imageSize.height
        let boundingBox = VNImageRectForNormalizedRect(observation.boundingBox, Int(w), Int(h))
        // 增加 5% padding
        let padded = boundingBox.insetBy(dx: -boundingBox.width * 0.05,
                                         dy: -boundingBox.height * 0.05)
            .intersection(CGRect(origin: .zero, size: imageSize))
        return cgImage.cropping(to: padded)
    }

    // MARK: - CoreImage 亮度/對比

    private static func adjustBrightnessContrast(_ image: UIImage,
                                                  brightness: Float,
                                                  contrast: Float) -> UIImage? {
        guard let cgImage = image.cgImage else { return nil }
        let ciImage = CIImage(cgImage: cgImage)
        let filter = CIFilter.colorControls()
        filter.inputImage = ciImage
        filter.brightness = brightness
        filter.contrast = contrast
        filter.saturation = 1.0

        let context = CIContext()
        guard let output = filter.outputImage,
              let result = context.createCGImage(output, from: output.extent) else { return nil }
        return UIImage(cgImage: result, scale: image.scale, orientation: image.imageOrientation)
    }
}
