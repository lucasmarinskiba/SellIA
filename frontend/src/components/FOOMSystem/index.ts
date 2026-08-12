/**
 * FOOM Double-Engine Components
 *
 * Generates FOOM on two levels:
 * 1. SellIA → Users (convert free → paid)
 * 2. Users → Their Customers (via shared FOOM content)
 *
 * Components:
 * - RealTimeFOOMDashboard: Live FOOM metrics
 * - CostOfDelayDisplay: Financial impact visualization
 * - SocialContentGenerator: Shareable FOOM content
 * - MicroCommitmentSequence: 7-step closing sequence
 */

export { RealTimeFOOMDashboard } from './RealTimeFOOMDashboard';
export { CostOfDelayDisplay } from './CostOfDelayDisplay';
export { SocialContentGenerator } from './SocialContentGenerator';
export { MicroCommitmentSequence } from './MicroCommitmentSequence';
