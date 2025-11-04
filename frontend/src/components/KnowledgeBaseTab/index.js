import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Button,
  Typography,
  Box,
  Chip,
  CircularProgress,
  LinearProgress,
} from "@material-ui/core";
import {
  CloudUpload,
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as FileIcon,
} from "@material-ui/icons";
import { makeStyles } from "@material-ui/core/styles";
import { toast } from "react-toastify";
import api from "../../services/api";
import toastError from "../../errors/toastError";
import ConfirmationModal from "../ConfirmationModal";

const useStyles = makeStyles((theme) => ({
  paper: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  uploadBox: {
    border: `2px dashed ${theme.palette.primary.main}`,
    borderRadius: theme.spacing(1),
    padding: theme.spacing(4),
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.3s",
    marginBottom: theme.spacing(3),
    "&:hover": {
      backgroundColor: theme.palette.action.hover,
      borderColor: theme.palette.primary.dark,
    },
  },
  uploadBoxActive: {
    backgroundColor: theme.palette.action.selected,
    borderColor: theme.palette.primary.dark,
  },
  fileIcon: {
    fontSize: 48,
    color: theme.palette.text.secondary,
    marginBottom: theme.spacing(1),
  },
  table: {
    minWidth: 650,
  },
  statusChip: {
    fontWeight: "bold",
  },
}));

const KnowledgeBaseTab = ({ teamId }) => {
  const classes = useStyles();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const fileInputRef = useRef(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/teams/${teamId}/knowledge`);
      setDocuments(data.knowledgeBases || []);
    } catch (err) {
      toastError(err);
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    if (teamId) {
      loadDocuments();
    }
  }, [teamId, loadDocuments]);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validar tipo
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];

    if (!allowedTypes.includes(file.type)) {
      toast.error("Tipo de arquivo não permitido. Use PDF, DOCX ou TXT.");
      return;
    }

    // Validar tamanho (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Arquivo muito grande. Tamanho máximo: 10MB");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await api.post(
        `/teams/${teamId}/knowledge/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(progress);
          },
        }
      );

      toast.success("Documento processado com sucesso!");
      loadDocuments();
      // Reset input
      event.target.value = null;
    } catch (err) {
      toastError(err);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteDocument = async (docId) => {
    try {
      await api.delete(`/knowledge/${docId}`);
      toast.success("Documento deletado com sucesso!");
      loadDocuments();
    } catch (err) {
      toastError(err);
    } finally {
      setConfirmModalOpen(false);
      setSelectedDocument(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case "pdf":
        return <PdfIcon style={{ color: "#d32f2f" }} />;
      case "docx":
        return <DescriptionIcon style={{ color: "#1976d2" }} />;
      case "txt":
        return <FileIcon style={{ color: "#757575" }} />;
      default:
        return <FileIcon />;
    }
  };

  return (
    <>
      <ConfirmationModal
        title="Deletar Documento"
        open={confirmModalOpen}
        onClose={() => {
          setConfirmModalOpen(false);
          setSelectedDocument(null);
        }}
        onConfirm={() => handleDeleteDocument(selectedDocument.id)}
      >
        Tem certeza que deseja deletar o documento "{selectedDocument?.filename}"?
        Esta ação não pode ser desfeita.
      </ConfirmationModal>

      <Paper className={classes.paper}>
        <Typography variant="h6" gutterBottom>
          Base de Conhecimento
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Faça upload de documentos (PDF, DOCX, TXT) para que os agentes possam
          consultar informações relevantes durante as conversas.
        </Typography>

        {/* Upload Area */}
        <Box className={classes.uploadBox}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            style={{ display: "none" }}
            onChange={handleFileSelect}
            disabled={uploading}
          />
          <CloudUpload className={classes.fileIcon} />
          {uploading ? (
            <>
              <Typography variant="body1" gutterBottom>
                Processando documento... {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </>
          ) : (
            <>
              <Typography variant="body1" gutterBottom>
                Selecione um arquivo para fazer upload
              </Typography>
              <Typography variant="caption" color="textSecondary" paragraph>
                Formatos aceitos: PDF, DOCX, TXT (máx. 10MB)
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<CloudUpload />}
                onClick={() => fileInputRef.current?.click()}
              >
                Selecionar Arquivo
              </Button>
            </>
          )}
        </Box>

        {/* Documents List */}
        {loading ? (
          <Box display="flex" justifyContent="center" padding={3}>
            <CircularProgress />
          </Box>
        ) : documents.length > 0 ? (
          <Table className={classes.table}>
            <TableHead>
              <TableRow>
                <TableCell>Tipo</TableCell>
                <TableCell>Nome do Arquivo</TableCell>
                <TableCell align="right">Tamanho</TableCell>
                <TableCell align="right">Chunks</TableCell>
                <TableCell align="right">Palavras</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell align="center">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{getFileIcon(doc.fileType)}</TableCell>
                  <TableCell>{doc.filename}</TableCell>
                  <TableCell align="right">
                    {formatFileSize(doc.fileSize)}
                  </TableCell>
                  <TableCell align="right">{doc.chunksCount || 0}</TableCell>
                  <TableCell align="right">{doc.wordCount || 0}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={doc.status === "ready" ? "Pronto" : "Processando"}
                      color={doc.status === "ready" ? "primary" : "default"}
                      size="small"
                      className={classes.statusChip}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedDocument(doc);
                        setConfirmModalOpen(true);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Box textAlign="center" padding={3}>
            <Typography variant="body2" color="textSecondary">
              Nenhum documento adicionado ainda. Faça upload do primeiro
              documento acima.
            </Typography>
          </Box>
        )}
      </Paper>
    </>
  );
};

export default KnowledgeBaseTab;
