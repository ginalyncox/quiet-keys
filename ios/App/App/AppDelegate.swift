import UIKit
import Capacitor
import CoreMIDI

/// Listens to any USB (or other Core MIDI) keyboard and reports each key press.
/// Wired MIDI needs no permission prompt on iPad or iPhone.
final class MidiListener {
    static let shared = MidiListener()

    var onNote: ((Int) -> Void)?
    var onDevices: ((Int) -> Void)?

    private var client = MIDIClientRef()
    private var port = MIDIPortRef()
    private var started = false

    func start() {
        if started { connectAll(); return }
        started = true

        MIDIClientCreateWithBlock("Quiet Keys" as CFString, &client) { [weak self] _ in
            // A keyboard was plugged in or removed.
            DispatchQueue.main.async { self?.connectAll() }
        }
        MIDIInputPortCreateWithProtocol(client, "Quiet Keys In" as CFString, ._1_0, &port) { [weak self] eventList, _ in
            self?.handle(eventList)
        }
        connectAll()
    }

    private func connectAll() {
        let count = MIDIGetNumberOfSources()
        for index in 0..<count {
            MIDIPortConnectSource(port, MIDIGetSource(index), nil)
        }
        onDevices?(count)
    }

    private func handle(_ eventList: UnsafePointer<MIDIEventList>) {
        var pressed: [Int] = []
        for packet in eventList.unsafeSequence() {
            let wordCount = Int(packet.pointee.wordCount)
            if wordCount == 0 { continue }
            var words = packet.pointee.words
            withUnsafePointer(to: &words) { tuple in
                tuple.withMemoryRebound(to: UInt32.self, capacity: 64) { buffer in
                    for index in 0..<min(wordCount, 64) {
                        let word = buffer[index]
                        let messageType = (word >> 28) & 0xF   // 2 = MIDI 1.0 channel message
                        let status = (word >> 20) & 0xF        // 9 = note on
                        let note = Int((word >> 8) & 0x7F)
                        let velocity = Int(word & 0x7F)
                        if messageType == 0x2 && status == 0x9 && velocity > 0 {
                            pressed.append(note)
                        }
                    }
                }
            }
        }
        if pressed.isEmpty { return }
        DispatchQueue.main.async { [weak self] in
            for note in pressed { self?.onNote?(note) }
        }
    }
}

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        MidiListener.shared.onNote = { [weak self] note in
            self?.sendToPage("window.quietKeysNote && window.quietKeysNote(\(note));")
        }
        MidiListener.shared.onDevices = { [weak self] count in
            self?.sendToPage("window.quietKeysDevices && window.quietKeysDevices(\(count));")
        }
        return true
    }

    /// Runs a small piece of JavaScript in the lesson page.
    private func sendToPage(_ script: String) {
        guard let controller = window?.rootViewController as? CAPBridgeViewController else { return }
        controller.bridge?.webView?.evaluateJavaScript(script, completionHandler: nil)
    }

    func applicationWillResignActive(_ application: UIApplication) {
    }

    func applicationDidEnterBackground(_ application: UIApplication) {
    }

    func applicationWillEnterForeground(_ application: UIApplication) {
    }

    func applicationDidBecomeActive(_ application: UIApplication) {
        // Start (or re-check) the keyboard once the page has had a moment to load.
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            MidiListener.shared.start()
        }
    }

    func applicationWillTerminate(_ application: UIApplication) {
    }

    func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
        return ApplicationDelegateProxy.shared.application(app, open: url, options: options)
    }

    func application(_ application: UIApplication, continue userActivity: NSUserActivity, restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
        return ApplicationDelegateProxy.shared.application(application, continue: userActivity, restorationHandler: restorationHandler)
    }

}
