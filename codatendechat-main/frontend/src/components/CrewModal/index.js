import React, { useState, useEffect } from "react";
import * as Yup from "yup";
import { Formik, Form, Field, FieldArray } from "formik";
import { toast } from "react-toastify";
import { makeStyles } from "@material-ui/core/styles";
import { green } from "@material-ui/core/colors";
import {
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  CircularProgress,
  IconButton,
  Box,
  Typography,
  Divider,
  Checkbox,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from "@material-ui/core";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  CloudUpload as CloudUploadIcon,
  Description as DescriptionIcon,
} from "@material-ui/icons";

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
  agentCard: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: 4,
    position: "relative",
  },
  deleteButton: {
    position: "absolute",
    top: 8,
    right: 8,
  },
  sectionTitle: {
    fontWeight: 600,
    fontSize: "0.875rem",
    marginBottom: theme.spacing(1),
    marginTop: theme.spacing(2),
  },
  accordion: {
    marginBottom: theme.spacing(1),
    "&:before": {
      display: "none",
    },
  },
  accordionSummary: {
    backgroundColor: theme.palette.grey[50],
    borderRadius: 4,
  },
  uploadArea: {
    border: `2px dashed ${theme.palette.divider}`,
    borderRadius: 4,
    padding: theme.spacing(4),
    textAlign: "center",
    cursor: "pointer",
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
    "&:hover": {
      backgroundColor: theme.palette.action.hover,
    },
  },
  knowledgeItem: {
    marginBottom: theme.spacing(1),
  },
}));

const AgentSchema = Yup.object().shape({
  name: Yup.string().required("Nome é obrigatório"),
  role: Yup.string().required("Função é obrigatória"),
  goal: Yup.string().required("Objetivo é obrigatório"),
  backstory: Yup.string().required("História é obrigatória"),
  useKnowledge: Yup.boolean(),
  keywords: Yup.string(),
  customInstructions: Yup.string(),
  persona: Yup.string(),
  guardrailsDo: Yup.string(),
  guardrailsDont: Yup.string(),
});

const CrewSchema = Yup.object().shape({
  name: Yup.string()
    .min(2, "Nome muito curto")
    .max(100, "Nome muito longo")
    .required("Nome é obrigatório"),
  description: Yup.string()
    .min(10, "Descrição muito curta")
    .max(500, "Descrição muito longa")
    .required("Descrição é obrigatória"),
  agents: Yup.array().of(AgentSchema).min(1, "Pelo menos um agente é necessário"),
});

const CrewModal = ({ open, onClose, crewId, onSave }) => {
  const classes = useStyles();
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [knowledgeFiles, setKnowledgeFiles] = useState([]);
  const [initialValues, setInitialValues] = useState({
    name: "",
    description: "",
    agents: [
      {
        name: "",
        role: "",
        goal: "",
        backstory: "",
        useKnowledge: false,
        keywords: "",
        customInstructions: "",
        persona: "",
        guardrailsDo: "",
        guardrailsDont: "",
      },
    ],
  });

  useEffect(() => {
    const fetchCrew = async () => {
      if (!crewId) {
        setInitialValues({
          name: "",
          description: "",
          agents: [
            {
              name: "",
              role: "",
              goal: "",
              backstory: "",
              useKnowledge: false,
              keywords: "",
              customInstructions: "",
              persona: "",
              guardrailsDo: "",
              guardrailsDont: "",
            },
          ],
        });
        return;
      }

      setLoading(true);
      try {
        const { data } = await api.get(`/crews/${crewId}`);

        // Converter agents de objeto para array ORDENADO por order
        const agentsArray = data.agents
          ? Object.entries(data.agents)
              .sort((a, b) => (a[1].order || 0) - (b[1].order || 0))
              .map(([key, agent]) => ({
                name: agent.name || "",
                role: agent.role || "",
                goal: agent.goal || "",
                backstory: agent.backstory || "",
                useKnowledge: agent.knowledgeDocuments?.length > 0 || false,
                keywords: (agent.keywords || []).join("\n"),
                customInstructions: agent.personality?.customInstructions || "",
                persona: agent.training?.persona || "",
                guardrailsDo: (agent.training?.guardrails?.do || []).join("\n"),
                guardrailsDont: (agent.training?.guardrails?.dont || []).join("\n"),
              }))
          : [{
              name: "",
              role: "",
              goal: "",
              backstory: "",
              useKnowledge: false,
              keywords: "",
              customInstructions: "",
              persona: "",
              guardrailsDo: "",
              guardrailsDont: "",
            }];

        setInitialValues({
          name: data.name || "",
          description: data.description || "",
          agents: agentsArray,
        });
      } catch (err) {
        toastError(err);
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      fetchCrew();
    }
  }, [crewId, open]);

  const handleClose = () => {
    onClose();
  };

  const handleSaveCrew = async (values) => {
    try {
      // Converter agents array para objeto com keys
      const agentsObject = {};
      values.agents.forEach((agent, idx) => {
        const agentId = `agent_${idx + 1}`;
        agentsObject[agentId] = {
          name: agent.name,
          role: agent.role,
          goal: agent.goal,
          backstory: agent.backstory,
          order: idx + 1,
          isActive: true,
          keywords: agent.keywords
            ? agent.keywords.split("\n").map(k => k.trim()).filter(k => k)
            : [],
          personality: {
            tone: "professional",
            traits: [],
            customInstructions: agent.customInstructions || "",
          },
          tools: [],
          toolConfigs: {},
          knowledgeDocuments: agent.useKnowledge ? [] : [],
          training: {
            guardrails: {
              do: agent.guardrailsDo
                ? agent.guardrailsDo.split("\n").map(l => l.trim()).filter(l => l)
                : [],
              dont: agent.guardrailsDont
                ? agent.guardrailsDont.split("\n").map(l => l.trim()).filter(l => l)
                : [],
            },
            persona: agent.persona || agent.backstory,
            examples: [],
          },
        };
      });

      const crewData = {
        name: values.name,
        description: values.description,
        agents: agentsObject,
      };

      if (crewId) {
        await api.put(`/crews/${crewId}`, crewData);
        toast.success("Equipe atualizada com sucesso!");
      } else {
        await api.post("/crews", crewData);
        toast.success("Equipe criada com sucesso!");
      }

      if (onSave) {
        onSave();
      }
      handleClose();
    } catch (err) {
      toastError(err);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !crewId) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadingFile(true);
      const { data } = await api.post(`/crews/${crewId}/knowledge/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setKnowledgeFiles(prev => [...prev, data]);
      toast.success("Arquivo enviado com sucesso!");
    } catch (err) {
      toastError(err);
    } finally {
      setUploadingFile(false);
      event.target.value = "";
    }
  };

  const handleDeleteKnowledge = async (fileId) => {
    if (!crewId) return;

    try {
      await api.delete(`/crews/${crewId}/knowledge/${fileId}`);
      setKnowledgeFiles(prev => prev.filter(f => f.id !== fileId));
      toast.success("Arquivo removido com sucesso!");
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle>
        {crewId ? "Editar Equipe" : "Nova Equipe"}
      </DialogTitle>

      {loading ? (
        <DialogContent dividers>
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        </DialogContent>
      ) : (
        <Formik
          initialValues={initialValues}
          enableReinitialize={true}
          validationSchema={CrewSchema}
          onSubmit={handleSaveCrew}
        >
          {({ touched, errors, isSubmitting, values }) => (
            <Form>
              <DialogContent dividers>
                {/* Nome e Descrição */}
                <div className={classes.root}>
                  <Field
                    as={TextField}
                    label="Nome da Equipe"
                    autoFocus
                    name="name"
                    error={touched.name && Boolean(errors.name)}
                    helperText={touched.name && errors.name}
                    variant="outlined"
                    margin="dense"
                    fullWidth
                    className={classes.textField}
                  />
                </div>
                <div className={classes.root}>
                  <Field
                    as={TextField}
                    label="Descrição"
                    name="description"
                    error={touched.description && Boolean(errors.description)}
                    helperText={touched.description && errors.description}
                    variant="outlined"
                    margin="dense"
                    multiline
                    rows={3}
                    fullWidth
                    className={classes.textField}
                  />
                </div>

                <Divider style={{ margin: "24px 0 16px 0" }} />

                {/* Lista de Agentes */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Agentes
                  </Typography>
                </Box>

                <FieldArray name="agents">
                  {({ push, remove }) => (
                    <>
                      {values.agents.map((agent, index) => (
                        <Accordion key={index} className={classes.accordion} defaultExpanded={index === 0}>
                          <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            className={classes.accordionSummary}
                          >
                            <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                              <Typography variant="subtitle1">
                                {agent.name || `Agente ${index + 1}`}
                              </Typography>
                              {values.agents.length > 1 && (
                                <IconButton
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    remove(index);
                                  }}
                                  color="secondary"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              )}
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Box width="100%">
                              {/* Informações Básicas */}
                              <Typography className={classes.sectionTitle}>
                                📋 Informações Básicas
                              </Typography>

                              <Field
                                as={TextField}
                                label="Nome do Agente"
                                name={`agents.${index}.name`}
                                error={
                                  touched.agents?.[index]?.name &&
                                  Boolean(errors.agents?.[index]?.name)
                                }
                                helperText={
                                  touched.agents?.[index]?.name &&
                                  errors.agents?.[index]?.name
                                }
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                size="small"
                              />

                              <Field
                                as={TextField}
                                label="Função (Role)"
                                name={`agents.${index}.role`}
                                error={
                                  touched.agents?.[index]?.role &&
                                  Boolean(errors.agents?.[index]?.role)
                                }
                                helperText={
                                  touched.agents?.[index]?.role &&
                                  errors.agents?.[index]?.role
                                }
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                size="small"
                              />

                              <Field
                                as={TextField}
                                label="Objetivo (Goal)"
                                name={`agents.${index}.goal`}
                                error={
                                  touched.agents?.[index]?.goal &&
                                  Boolean(errors.agents?.[index]?.goal)
                                }
                                helperText={
                                  touched.agents?.[index]?.goal &&
                                  errors.agents?.[index]?.goal
                                }
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={2}
                                size="small"
                              />

                              <Field
                                as={TextField}
                                label="História (Backstory)"
                                name={`agents.${index}.backstory`}
                                error={
                                  touched.agents?.[index]?.backstory &&
                                  Boolean(errors.agents?.[index]?.backstory)
                                }
                                helperText={
                                  touched.agents?.[index]?.backstory &&
                                  errors.agents?.[index]?.backstory
                                }
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                              />

                              <Field
                                as={TextField}
                                label="Keywords (uma por linha)"
                                name={`agents.${index}.keywords`}
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                                placeholder="palavra1&#10;palavra2&#10;palavra3"
                                helperText="Palavras-chave que ajudam a identificar quando usar este agente"
                              />

                              <Field
                                as={TextField}
                                label="Instruções Personalizadas"
                                name={`agents.${index}.customInstructions`}
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                                placeholder="Ex: Sempre finalize com uma pergunta. Nunca use termos técnicos..."
                                helperText="Instruções específicas de como o agente deve se comportar"
                              />

                              {/* Treinamento de Comportamento */}
                              <Typography className={classes.sectionTitle}>
                                🎭 Treinamento de Comportamento (Guardrails)
                              </Typography>

                              <Field
                                as={TextField}
                                label="Persona do Agente"
                                name={`agents.${index}.persona`}
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                                placeholder="Ex: Você é cordial e sempre confirma informações..."
                                helperText="Como o agente deve se apresentar e agir"
                              />

                              <Field
                                as={TextField}
                                label="Regras - O que FAZER"
                                name={`agents.${index}.guardrailsDo`}
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                                placeholder="Sempre confirme os dados&#10;Seja cordial&#10;Pergunte se pode ajudar em algo mais"
                                helperText="Uma regra por linha - comportamentos desejados"
                              />

                              <Field
                                as={TextField}
                                label="Regras - O que NÃO fazer"
                                name={`agents.${index}.guardrailsDont`}
                                variant="outlined"
                                margin="dense"
                                fullWidth
                                multiline
                                rows={3}
                                size="small"
                                placeholder="Nunca divulgue informações confidenciais&#10;Nunca use linguagem informal&#10;Nunca encerre sem confirmar"
                                helperText="Uma regra por linha - comportamentos a evitar"
                              />

                              {/* Ferramentas */}
                              <Typography className={classes.sectionTitle}>
                                🔧 Ferramentas Disponíveis
                              </Typography>

                              <Field name={`agents.${index}.useKnowledge`}>
                                {({ field }) => (
                                  <FormControlLabel
                                    control={
                                      <Checkbox
                                        {...field}
                                        checked={field.value}
                                        color="primary"
                                      />
                                    }
                                    label="📚 Usar base de conhecimento"
                                  />
                                )}
                              </Field>
                            </Box>
                          </AccordionDetails>
                        </Accordion>
                      ))}

                      <Button
                        variant="outlined"
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={() =>
                          push({
                            name: "",
                            role: "",
                            goal: "",
                            backstory: "",
                            useKnowledge: false,
                            keywords: "",
                            customInstructions: "",
                            persona: "",
                            guardrailsDo: "",
                            guardrailsDont: "",
                          })
                        }
                        fullWidth
                        style={{ marginTop: 16 }}
                      >
                        Adicionar Agente
                      </Button>

                      {typeof errors.agents === 'string' && (
                        <Typography color="error" variant="caption" display="block" style={{ marginTop: 8 }}>
                          {errors.agents}
                        </Typography>
                      )}
                    </>
                  )}
                </FieldArray>

                {/* Base de Conhecimento */}
                {crewId && (
                  <>
                    <Divider style={{ margin: "32px 0 24px 0" }} />

                    <Typography variant="h6" gutterBottom>
                      📚 Base de Conhecimento
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Faça upload de documentos para a equipe consultar (PDF, TXT, DOC, DOCX)
                    </Typography>

                    <input
                      accept=".pdf,.txt,.doc,.docx"
                      style={{ display: 'none' }}
                      id="knowledge-upload"
                      type="file"
                      onChange={handleFileUpload}
                      disabled={uploadingFile}
                    />
                    <label htmlFor="knowledge-upload">
                      <Paper className={classes.uploadArea} elevation={0} component="div">
                        <CloudUploadIcon style={{ fontSize: 48, color: '#666' }} />
                        <Typography variant="body1" gutterBottom>
                          {uploadingFile ? "Enviando..." : "Clique para fazer upload"}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Arraste um arquivo ou clique aqui
                        </Typography>
                      </Paper>
                    </label>

                    {knowledgeFiles.length > 0 && (
                      <Box mt={3}>
                        <Typography variant="subtitle1" gutterBottom>
                          Documentos Carregados ({knowledgeFiles.length})
                        </Typography>
                        <List>
                          {knowledgeFiles.map((file) => (
                            <Paper key={file.id} className={classes.knowledgeItem} elevation={1}>
                              <ListItem>
                                <DescriptionIcon color="primary" style={{ marginRight: 16 }} />
                                <ListItemText
                                  primary={file.name}
                                  secondary={`Tamanho: ${(file.size / 1024).toFixed(2)} KB`}
                                />
                                <ListItemSecondaryAction>
                                  <IconButton edge="end" onClick={() => handleDeleteKnowledge(file.id)} color="secondary">
                                    <DeleteIcon />
                                  </IconButton>
                                </ListItemSecondaryAction>
                              </ListItem>
                            </Paper>
                          ))}
                        </List>
                      </Box>
                    )}
                  </>
                )}
              </DialogContent>
              <DialogActions>
                <Button
                  onClick={handleClose}
                  color="secondary"
                  disabled={isSubmitting}
                  variant="outlined"
                >
                  Cancelar
                </Button>
                <div className={classes.btnWrapper}>
                  <Button
                    type="submit"
                    color="primary"
                    disabled={isSubmitting}
                    variant="contained"
                  >
                    {crewId ? "Salvar" : "Criar"}
                  </Button>
                  {isSubmitting && (
                    <CircularProgress
                      size={24}
                      className={classes.buttonProgress}
                    />
                  )}
                </div>
              </DialogActions>
            </Form>
          )}
        </Formik>
      )}
    </Dialog>
  );
};

export default CrewModal;
