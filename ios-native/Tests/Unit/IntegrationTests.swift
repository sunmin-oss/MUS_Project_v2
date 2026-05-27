import XCTest
@testable import MUS_iOS

/// Integration tests — skipped unless BACKEND_URL env var is set
final class IntegrationTests: XCTestCase {

    var backendURL: String { ProcessInfo.processInfo.environment["BACKEND_URL"] ?? "" }
    var realClient: RealAPIClient?

    override func setUp() {
        super.setUp()
        guard !backendURL.isEmpty else { return }
        realClient = RealAPIClient(baseURL: URL(string: backendURL)!)
    }

    func testRecognizeDrug() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        // 1x1 white JPEG
        let imageData = Data(base64Encoded: "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wgARCAABAAEDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAABgUE/9oACAEBAAAAAN5f/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAQF/9oACAECEAAAAF5f/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAME/9oACAEDEAAAACVf/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPwBn/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwBn/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwBn/9k=")!
        let result = try await client.recognizeDrug(imageData: imageData)
        XCTAssertFalse(result.requestId.isEmpty)
    }

    func testFetchDrug() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        let drug = try await client.fetchDrug(id: 101)
        XCTAssertEqual(drug.id, 101)
    }

    func testMedicationsCRUD() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        let profileId = "p1"
        let meds = try await client.fetchMedications(profileId: profileId)
        XCTAssertNotNil(meds)
    }

    func testSafetyCheck() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        let alerts = try await client.checkSafety(profileId: "p1", drugIds: [101, 103])
        XCTAssertNotNil(alerts)
    }

    func testNearbyPharmacies() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        let pharmacies = try await client.fetchNearbyPharmacies(latitude: 25.04, longitude: 121.51, radius: 1000)
        XCTAssertNotNil(pharmacies)
    }

    func testSearchDrugs() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        let drugs = try await client.searchDrugs(query: "普拿疼", limit: 5)
        XCTAssertFalse(drugs.isEmpty)
    }

    func testAllEndpointsSmoke() async throws {
        guard let client = realClient else { throw XCTSkip("BACKEND_URL not set") }
        _ = try await client.fetchProfiles()
        _ = try await client.fetchConsultations()
    }
}
