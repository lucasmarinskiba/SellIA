// Registers @testing-library/jest-dom's ambient Matchers augmentation
// (toBeInTheDocument, toHaveClass, etc.) for `tsc --noEmit`.
//
// jest.setup.js already does `require('@testing-library/jest-dom')` at
// runtime, but that file is plain JS and isn't part of the TypeScript
// program (tsconfig's `include` only lists **/*.ts / **/*.tsx), so its
// side-effecting type augmentation was invisible to the type checker.
// This .d.ts *is* picked up by that same include glob, which is all a
// declaration file needs to register the augmentation project-wide.
import "@testing-library/jest-dom";
