import React, { useState, useEffect } from "react";
import * as Yup from "yup";
import { Formik, Form, Field, FieldArray } from "formik";
import { toast } from "react-toastify";

import { makeStyles } from "@material-ui/core/styles";
import { green } from "@material-ui/core/colors";
import Button from "@material-ui/core/Button";
import TextField from "@material-ui/core/TextField";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import CircularProgress from "@material-ui/core/CircularProgress";
import {
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Chip,
  Typography,
  Checkbox,
  FormControlLabel,
  FormGroup,
  FormLabel,
} from "@material-ui/core";
import { Add, Delete, CloudUpload, InsertDriveFile, Image } from "@material-ui/icons";

import { i18n } from "../../translate/i18n";
import api from "../../services/api";
import toastError from "../../errors/toastError";

const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
    flexWrap: "wrap",
  },
  textField: {
    marginRight: theme.spacing(1),
    flex: 1,
  },
  btnWrapper: {
    position: "relative",
  },
  buttonProgress: {
    color: green[500],
    position: "absolute",
    top: "50%",
    left: "50%",
    marginTop: -12,
    marginLeft: -12,
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
  listItem: {
    display: "flex",
    alignItems: "center",
    marginBottom: theme.spacing(1),
  },
  fileSection: {
    marginTop: theme.spacing(2),
    padding: theme.spacing(2),
    border: "1px solid #e0e0e0",
    borderRadius: 8,
    backgroundColor: "#fafafa",
  },
  fileList: {
    marginTop: theme.spacing(1),
  },
  fileItem: {
    display: "flex",
    alignItems: "center",
    padding: theme.spacing(1),
    marginBottom: theme.spacing(1),
    backgroundColor: "#fff",
    borderRadius: 4,
    border: "1px solid #e0e0e0",
  },
  fileIcon: {
    marginRight: theme.spacing(1),
    color: "#666",
  },
  fileInfo: {
    flex: 1,
  },
  uploadButton: {
    marginTop: theme.spacing(1),
  },
  uploadInput: {
    display: "none",
  },
}));

const AgentSchema = Yup.object().shape({
  name: Yup.string()
    .min(2, "Nome muito curto")
    .max(100, "Nome muito longo")
    .required("Nome é obrigatório"),
});

const AgentModal = ({ open, onClose, agentId, teamId }) => {
  const classes = useStyles();

  const initialState = {
    name: "",
    function: "",
    objective: "",
    backstory: "",
    keywords: [],
    customInstructions: "",
    persona: "",
    doList: [],
    dontList: [],
    aiProvider: "crewai",
    isActive: true,
    teamId: teamId || null,
    useKnowledgeBase: false,
    knowledgeBaseIds: [],
  };

  const [agent, setAgent] = useState(initialState);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [agentFiles, setAgentFiles] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    const fetchAgent = async () => {
      if (!agentId) {
        // Se não tem agentId, resetar para estado inicial
        setAgent({...initialState, teamId: teamId || null});
        return;
      }
      try {
        const { data } = await api.get(`/agents/${agentId}`);
        setAgent({
          name: data.name,
          function: data.function || "",
          objective: data.objective || "",
          backstory: data.backstory || "",
          keywords: data.keywords || [],
          customInstructions: data.customInstructions || "",
          persona: data.persona || "",
          doList: data.doList || [],
          dontList: data.dontList || [],
          aiProvider: data.aiProvider || "crewai",
          isActive: data.isActive,
          teamId: data.teamId || teamId || null,
          useKnowledgeBase: data.useKnowledgeBase || false,
          knowledgeBaseIds: data.knowledgeBases?.map(kb => kb.id) || [],
        });
      } catch (err) {
        toastError(err);
      }
    };
    fetchAgent();
  }, [agentId, teamId, open]);

  useEffect(() => {
    const fetchKnowledgeBases = async () => {
      if (!teamId) return;
      try {
        const { data } = await api.get(`/teams/${teamId}/knowledge`);
        setKnowledgeBases(data.knowledgeBases || []);
      } catch (err) {
        console.error("Erro ao carregar knowledge bases:", err);
      }
    };
    if (open) {
      fetchKnowledgeBases();
    }
  }, [teamId, open]);

  // Carregar arquivos do agente
  useEffect(() => {
    const fetchAgentFiles = async () => {
      if (!agentId) {
        setAgentFiles([]);
        return;
      }
      try {
        const { data } = await api.get(`/agents/${agentId}/files`);
        setAgentFiles(data);
      } catch (err) {
        console.error("Erro ao carregar arquivos do agente:", err);
      }
    };
    if (open && agentId) {
      fetchAgentFiles();
    }
  }, [agentId, open]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validar tipo
    const allowedTypes = ["application/pdf", "image/png", "image/jpeg", "image/jpg"];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Tipo de arquivo não permitido. Use PDF, PNG ou JPG.");
      return;
    }

    // Validar tamanho (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Arquivo muito grande. Máximo 10MB.");
      return;
    }

    const description = prompt("Digite uma descrição para o arquivo (ex: Cardápio, Tabela de Preços):");
    if (!description) {
      toast.warning("Upload cancelado - descrição é necessária.");
      return;
    }

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("description", description);

      const { data } = await api.post(`/agents/${agentId}/files`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setAgentFiles([data, ...agentFiles]);
      toast.success("Arquivo enviado com sucesso!");
    } catch (err) {
      toastError(err);
    } finally {
      setUploadingFile(false);
      event.target.value = "";
    }
  };

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm("Tem certeza que deseja excluir este arquivo?")) return;

    try {
      await api.delete(`/agent-files/${fileId}`);
      setAgentFiles(agentFiles.filter(f => f.id !== fileId));
      toast.success("Arquivo excluído com sucesso!");
    } catch (err) {
      toastError(err);
    }
  };

  const handleClose = () => {
    setAgent(initialState);
    onClose();
  };

  const handleSaveAgent = async (values) => {
    try {
      if (agentId) {
        await api.put(`/agents/${agentId}`, values);
        toast.success("Agente atualizado com sucesso!");
      } else {
        await api.post("/agents", values);
        toast.success("Agente criado com sucesso!");
      }
      handleClose();
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <div className={classes.root}>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth scroll="paper">
        <DialogTitle>
          {agentId ? "Editar Agente" : "Adicionar Agente"}
        </DialogTitle>
        <Formik
          initialValues={agent}
          enableReinitialize={true}
          validationSchema={AgentSchema}
          onSubmit={(values, actions) => {
            setTimeout(() => {
              handleSaveAgent(values);
              actions.setSubmitting(false);
            }, 400);
          }}
        >
          {({ values, errors, touched, isSubmitting, setFieldValue }) => (
            <Form>
              <DialogContent dividers>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={8}>
                    <Field
                      as={TextField}
                      label="Nome do Agente"
                      name="name"
                      error={touched.name && Boolean(errors.name)}
                      helperText={touched.name && errors.name}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                      required
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      label="Função"
                      name="function"
                      multiline
                      rows={2}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      label="Objetivo"
                      name="objective"
                      multiline
                      rows={2}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      label="História/Contexto"
                      name="backstory"
                      multiline
                      rows={3}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      label="Persona"
                      name="persona"
                      multiline
                      rows={2}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Field
                      as={TextField}
                      label="Instruções Personalizadas"
                      name="customInstructions"
                      multiline
                      rows={3}
                      variant="outlined"
                      fullWidth
                      margin="dense"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Palavras-chave (para ativação do agente)
                    </Typography>
                    <FieldArray name="keywords">
                      {({ push, remove }) => (
                        <>
                          {values.keywords && values.keywords.map((keyword, index) => (
                            <Chip
                              key={index}
                              label={keyword}
                              onDelete={() => remove(index)}
                              style={{ margin: 4 }}
                            />
                          ))}
                          <Button
                            size="small"
                            onClick={() => {
                              const word = prompt("Digite a palavra-chave:");
                              if (word) push(word);
                            }}
                            startIcon={<Add />}
                          >
                            Adicionar Keyword
                          </Button>
                        </>
                      )}
                    </FieldArray>
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      O que o agente DEVE fazer
                    </Typography>
                    <FieldArray name="doList">
                      {({ push, remove }) => (
                        <>
                          {values.doList && values.doList.map((item, index) => (
                            <div key={index} className={classes.listItem}>
                              <TextField
                                value={item}
                                onChange={(e) => setFieldValue(`doList.${index}`, e.target.value)}
                                variant="outlined"
                                size="small"
                                fullWidth
                                margin="dense"
                              />
                              <IconButton onClick={() => remove(index)} size="small">
                                <Delete />
                              </IconButton>
                            </div>
                          ))}
                          <Button
                            size="small"
                            onClick={() => push("")}
                            startIcon={<Add />}
                          >
                            Adicionar regra
                          </Button>
                        </>
                      )}
                    </FieldArray>
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      O que o agente NÃO DEVE fazer
                    </Typography>
                    <FieldArray name="dontList">
                      {({ push, remove }) => (
                        <>
                          {values.dontList && values.dontList.map((item, index) => (
                            <div key={index} className={classes.listItem}>
                              <TextField
                                value={item}
                                onChange={(e) => setFieldValue(`dontList.${index}`, e.target.value)}
                                variant="outlined"
                                size="small"
                                fullWidth
                                margin="dense"
                              />
                              <IconButton onClick={() => remove(index)} size="small">
                                <Delete />
                              </IconButton>
                            </div>
                          ))}
                          <Button
                            size="small"
                            onClick={() => push("")}
                            startIcon={<Add />}
                          >
                            Adicionar regra
                          </Button>
                        </>
                      )}
                    </FieldArray>
                  </Grid>

                  {/* Knowledge Base Configuration */}
                  {knowledgeBases.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom style={{ marginTop: 16 }}>
                        Base de Conhecimento
                      </Typography>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={values.useKnowledgeBase}
                            onChange={(e) => {
                              setFieldValue("useKnowledgeBase", e.target.checked);
                              if (!e.target.checked) {
                                setFieldValue("knowledgeBaseIds", []);
                              }
                            }}
                            color="primary"
                          />
                        }
                        label="Usar Base de Conhecimento"
                      />
                      {values.useKnowledgeBase && (
                        <FormGroup style={{ marginLeft: 32, marginTop: 8 }}>
                          <FormLabel component="legend" style={{ fontSize: 14, marginBottom: 8 }}>
                            Selecione os documentos que este agente pode consultar:
                          </FormLabel>
                          {knowledgeBases.map((kb) => (
                            <FormControlLabel
                              key={kb.id}
                              control={
                                <Checkbox
                                  checked={values.knowledgeBaseIds.includes(kb.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setFieldValue("knowledgeBaseIds", [
                                        ...values.knowledgeBaseIds,
                                        kb.id,
                                      ]);
                                    } else {
                                      setFieldValue(
                                        "knowledgeBaseIds",
                                        values.knowledgeBaseIds.filter((id) => id !== kb.id)
                                      );
                                    }
                                  }}
                                  color="primary"
                                  size="small"
                                />
                              }
                              label={
                                <span style={{ fontSize: 14 }}>
                                  {kb.filename} ({kb.fileType.toUpperCase()} - {kb.chunksCount} chunks)
                                </span>
                              }
                            />
                          ))}
                        </FormGroup>
                      )}
                    </Grid>
                  )}

                  {/* Arquivos do Agente - só mostra se estiver editando (agentId existe) */}
                  {agentId && (
                    <Grid item xs={12}>
                      <div className={classes.fileSection}>
                        <Typography variant="subtitle1" gutterBottom style={{ fontWeight: "bold" }}>
                          Arquivos do Agente
                        </Typography>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          Arquivos que o agente pode enviar durante conversas no WhatsApp.
                          Use [SEND_FILE:id] na resposta para enviar.
                        </Typography>

                        {/* Lista de arquivos */}
                        <div className={classes.fileList}>
                          {agentFiles.length === 0 ? (
                            <Typography variant="body2" color="textSecondary" style={{ fontStyle: "italic" }}>
                              Nenhum arquivo cadastrado
                            </Typography>
                          ) : (
                            agentFiles.map((file) => (
                              <div key={file.id} className={classes.fileItem}>
                                {file.fileType === "pdf" ? (
                                  <InsertDriveFile className={classes.fileIcon} style={{ color: "#d32f2f" }} />
                                ) : (
                                  <Image className={classes.fileIcon} style={{ color: "#1976d2" }} />
                                )}
                                <div className={classes.fileInfo}>
                                  <Typography variant="body2" style={{ fontWeight: "bold" }}>
                                    [SEND_FILE:{file.id}] {file.description || file.originalName}
                                  </Typography>
                                  <Typography variant="caption" color="textSecondary">
                                    {file.originalName} ({file.fileType.toUpperCase()})
                                  </Typography>
                                </div>
                                <IconButton
                                  size="small"
                                  onClick={() => handleDeleteFile(file.id)}
                                  style={{ color: "#d32f2f" }}
                                >
                                  <Delete />
                                </IconButton>
                              </div>
                            ))
                          )}
                        </div>

                        {/* Botão de upload */}
                        <input
                          accept=".pdf,.png,.jpg,.jpeg"
                          className={classes.uploadInput}
                          id="agent-file-upload"
                          type="file"
                          onChange={handleFileUpload}
                          disabled={uploadingFile}
                        />
                        <label htmlFor="agent-file-upload">
                          <Button
                            variant="outlined"
                            color="primary"
                            component="span"
                            startIcon={uploadingFile ? <CircularProgress size={20} /> : <CloudUpload />}
                            disabled={uploadingFile}
                            className={classes.uploadButton}
                          >
                            {uploadingFile ? "Enviando..." : "Adicionar Arquivo"}
                          </Button>
                        </label>
                        <Typography variant="caption" color="textSecondary" style={{ marginLeft: 8 }}>
                          PDF, PNG ou JPG (max 10MB)
                        </Typography>
                      </div>
                    </Grid>
                  )}
                </Grid>
              </DialogContent>
              <DialogActions>
                <Button onClick={handleClose} color="secondary" disabled={isSubmitting}>
                  Cancelar
                </Button>
                <div className={classes.btnWrapper}>
                  <Button
                    type="submit"
                    color="primary"
                    disabled={isSubmitting}
                    variant="contained"
                  >
                    {agentId ? "Salvar" : "Adicionar"}
                  </Button>
                  {isSubmitting && (
                    <CircularProgress size={24} className={classes.buttonProgress} />
                  )}
                </div>
              </DialogActions>
            </Form>
          )}
        </Formik>
      </Dialog>
    </div>
  );
};

export default AgentModal;
