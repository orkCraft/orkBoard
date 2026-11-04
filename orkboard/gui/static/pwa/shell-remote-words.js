// What the phone says of its way through the project's remote (docs/specs/136-the-phone-through-the-projects-remote.md C, decisions §243), in one place: the lines
// of §243.6 and §243.7 are the spec's, word for word. *inbox*, *taken* and the branch names are names and stay as they are; the interface says goal and party.

export const TOKEN_CAN = "This token can change any file of the repository, the code too; Orkboard writes only orkboard/inbox. Make one for this repository alone, "
  + "with Contents: read and write. A rule on main that asks for a pull request keeps the code safe.";
export const TOKEN_KEPT = "Kept on this phone in the app's storage; the app from the store will keep it in the phone's keychain.";
export const PUBLIC = "This repository is public: goals sent through it would be seen by everyone. Make it private, or use the phone at home.";
export const NO_WRITE = "This token cannot write to the repository";
export const READY = "Ready: goals go through orkboard/inbox when your computer cannot be reached";
export const NO_REPO = "Name the repository as owner/name";
export const NO_TOKEN = "Paste the token";
export const NOT_FOUND = "This repository was not found, or this token cannot see it";
export const REFUSED = "The token was refused: give a new one in Settings";
export const SENT = "Sent through your repository: your computer or a cloud session will take it";
export const WAITS = "Waits for the network";
export const SET_REPO = "Set your repository in Settings to send goals while your computer is away";
export const WAITING = "Waiting to be taken: your computer or a cloud session will read it";
export const NEEDS_COMPUTER = "Needs your computer";
export const OFFLINE_CHECK = "Could not reach GitHub: check the network and try again";
export const NO_ROOM = "This phone has no room to keep it: free some space and send it again";

/** *As of 14:02*: when the journal was written, never as if it were now. */
export const asOf = (clock) => `As of ${clock}`;
/** *GitHub asks us to wait till 14:30*. */
export const waitTill = (clock) => `GitHub asks us to wait till ${clock}`;
