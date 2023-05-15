// swift-tools-version: 5.7
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription
import Foundation

var magic = true

var allSources = false
if ProcessInfo.processInfo.environment["ALL_SOURCES"] == "1" {
	allSources = true
}
let sources: [String] = [ "messenger", "payments" ]

var appTarget: PackageDescription.Target = .executableTarget(
	name: "app",
	dependencies: [],
	path: "app/Sources")

var package = Package(
    name: "app",
	dependencies: [],
	targets: [appTarget]
)

print("...")

func getCommitSHA(for dir: String) -> String? {
    let process = Process()
    let pipe = Pipe()

    let currentDir = URL(fileURLWithPath: #file).deletingLastPathComponent().path
    process.currentDirectoryPath = currentDir
    process.launchPath = "/usr/bin/env"
    process.arguments = ["git", "log", "--pretty=format:%H", "-1", "--", dir]
    process.standardOutput = pipe
    process.launch()

    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)

    return output
}

func add(module name: String, dependencies: [String] = []) {
	var binary = true
	if allSources {
		binary = false
	}
	for module in sources {
		if module == name {
			binary = false
		}
	}

    let sha = getCommitSHA(for: name)
    if binary && sha == nil && magic == false {
        print("Missing xcframework for \(name) at \(sha). Fallback to sources. Update cache using update_cache.py")
    }

	if binary, magic == true {
        package.targets.append(.binaryTarget(name: name, path: name + "/" + name + ".xcframework"))
    } else if binary, let sha {
        print("binary – \(name) – sha: \(sha)")
        package.targets.append(.binaryTarget(name: name, path: "binaries/\(sha)/\(name).xcframework"))
	} else {
		print("sources – \(name)")
		let target: PackageDescription.Target = .target(name: name, dependencies: [], path: name + "/Sources")
		for dependency in dependencies {
			target.dependencies.append(.byName(name: dependency))
		}

		package.targets.append(target)
		package.targets.append(.testTarget(
			name: name + "Tests", dependencies: [.byName(name: name)], path: name + "/Tests")
		)
	}
	appTarget.dependencies.append(.byName(name: name))

	package.products.append(.library(name: name, targets: [name]))
}

add(module: "networking")
add(module: "payments", dependencies: ["networking"])
add(module: "messenger", dependencies: ["networking", "payments"])


if ProcessInfo.processInfo.environment["NO_MAGIC"] == "1" { magic = false }
if magic {
	let currentDir = URL(fileURLWithPath: #file).deletingLastPathComponent().path
	// при изменении sources должен тригерится git clone, поэтому путь до репо содержит "чексумму" массива sources
	let sourcesString = sources.joined(separator: "_")
	print("git://localhost:12345/\(currentDir)/__dummy__\(sourcesString)")
	package.dependencies.append(.package(url: "git://localhost:12345/\(currentDir)/__dummy__\(sourcesString)", branch: "master"))
}
