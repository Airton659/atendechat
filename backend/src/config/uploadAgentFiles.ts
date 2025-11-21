import path from "path";
import multer from "multer";
import fs from "fs";

const publicFolder = path.resolve(__dirname, "..", "..", "public");
const agentFilesFolder = path.resolve(publicFolder, "agent-files");

// Criar pasta se não existir
if (!fs.existsSync(agentFilesFolder)) {
  fs.mkdirSync(agentFilesFolder, { recursive: true });
  fs.chmodSync(agentFilesFolder, 0o777);
}

export default {
  directory: agentFilesFolder,
  storage: multer.diskStorage({
    destination: function (req, file, cb) {
      if (!fs.existsSync(agentFilesFolder)) {
        fs.mkdirSync(agentFilesFolder, { recursive: true });
        fs.chmodSync(agentFilesFolder, 0o777);
      }
      return cb(null, agentFilesFolder);
    },
    filename(req, file, cb) {
      const timestamp = new Date().getTime();
      const sanitizedName = file.originalname.replace(/\//g, '-').replace(/ /g, "_");
      const fileName = `${timestamp}_${sanitizedName}`;
      return cb(null, fileName);
    }
  }),
  fileFilter: (req: any, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
    const allowedMimeTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
      "image/jpg"
    ];

    if (allowedMimeTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Tipo de arquivo não permitido. Use PDF, PNG ou JPG."));
    }
  }
};
