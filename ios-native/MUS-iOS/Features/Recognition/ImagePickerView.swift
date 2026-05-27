import SwiftUI
import PhotosUI
import AVFoundation

/// 相機 + 相簿選取器，回傳原始 UIImage
struct ImagePickerView: View {
    @Binding var selectedImage: UIImage?
    @State private var showPicker = false
    @State private var showCamera = false
    @State private var showSourceSheet = false
    @State private var cameraUnavailable = false

    var body: some View {
        VStack(spacing: DesignSpacing.md) {
            if let image = selectedImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 260)
                    .clipShape(RoundedRectangle(cornerRadius: DesignRadius.lg))
                    .overlay(alignment: .topTrailing) {
                        Button { selectedImage = nil } label: {
                            Image(systemName: "xmark.circle.fill")
                                .font(.title2)
                                .foregroundStyle(.white.shadow(.drop(radius: 2)))
                                .padding(8)
                        }
                    }
            } else {
                ZStack {
                    RoundedRectangle(cornerRadius: DesignRadius.lg)
                        .fill(Color(.secondarySystemBackground))
                        .frame(maxWidth: .infinity, minHeight: 200)
                    VStack(spacing: DesignSpacing.sm) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: 44))
                            .foregroundStyle(DesignColors.textSecondary)
                        Text("recognition.picker.hint")
                            .font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                }
                .onTapGesture { showSourceSheet = true }
            }

            HStack(spacing: DesignSpacing.sm) {
                PrimaryButton("recognition.action.camera",
                              systemImage: "camera.fill") {
                    if UIImagePickerController.isSourceTypeAvailable(.camera) {
                        showCamera = true
                    } else {
                        cameraUnavailable = true
                    }
                }
                PrimaryButton("recognition.action.library",
                              systemImage: "photo.on.rectangle",
                              style: .bordered) {
                    showPicker = true
                }
            }
        }
        .sheet(isPresented: $showPicker) {
            PhotoLibraryPicker(image: $selectedImage)
        }
        .fullScreenCover(isPresented: $showCamera) {
            CameraView(image: $selectedImage)
                .ignoresSafeArea()
        }
        .confirmationDialog("recognition.source.title",
                             isPresented: $showSourceSheet,
                             titleVisibility: .visible) {
            Button("recognition.action.camera") {
                if UIImagePickerController.isSourceTypeAvailable(.camera) {
                    showCamera = true
                } else { cameraUnavailable = true }
            }
            Button("recognition.action.library") { showPicker = true }
        }
        .alert("recognition.camera.unavailable", isPresented: $cameraUnavailable) {
            Button("common.ok", role: .cancel) {}
        }
    }
}

// MARK: - Photo Library Picker (PHPickerViewController)

struct PhotoLibraryPicker: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.selectionLimit = 1
        config.filter = .images
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: PhotoLibraryPicker
        init(_ parent: PhotoLibraryPicker) { self.parent = parent }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.dismiss()
            guard let provider = results.first?.itemProvider,
                  provider.canLoadObject(ofClass: UIImage.self) else { return }
            provider.loadObject(ofClass: UIImage.self) { [weak self] object, _ in
                DispatchQueue.main.async {
                    self?.parent.image = object as? UIImage
                }
            }
        }
    }
}

// MARK: - Camera View (AVFoundation via UIImagePickerController)

struct CameraView: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.cameraCaptureMode = .photo
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: CameraView
        init(_ parent: CameraView) { self.parent = parent }

        func imagePickerController(_ picker: UIImagePickerController,
                                   didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            parent.image = info[.originalImage] as? UIImage
            parent.dismiss()
        }
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}
