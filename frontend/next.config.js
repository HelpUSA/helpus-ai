const { execSync } = require('child_process')

const appVersion = process.env.npm_package_version || '1.0.0'
const appCommit = process.env.VERCEL_GIT_COMMIT_SHA || (() => {
 try {
 return execSync('git rev-parse --short HEAD').toString().trim()
 } catch {
 return 'local'
 }
})()

/** @type {import('next').NextConfig} */
const nextConfig = {
 reactStrictMode: true,
 env: {
 NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
 NEXT_PUBLIC_APP_VERSION: appVersion,
 NEXT_PUBLIC_APP_COMMIT: appCommit.slice(0, 7),
 },
}

module.exports = nextConfig
