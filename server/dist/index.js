"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
require("dotenv/config");
const app_1 = __importDefault(require("./app"));
const routes_1 = __importDefault(require("./routes/routes"));
const PORT = process.env.PORT || 5000;
app_1.default.use("/api", routes_1.default);
app_1.default.use("/", (req, res) => {
    res.send("Hello World!");
});
app_1.default.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
//# sourceMappingURL=index.js.map