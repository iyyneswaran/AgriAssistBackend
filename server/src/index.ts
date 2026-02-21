import "dotenv/config";
import app from "./app";
import routes from "./routes/routes";
import { Request, Response } from "express";

const PORT = process.env.PORT || 5000;

app.use("/api", routes);
app.use("/", (req: Request, res: Response) => {
  res.send("Hello World!");
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});