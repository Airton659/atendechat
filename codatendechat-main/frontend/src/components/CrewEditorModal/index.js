import React, { useState, useEffect } from "react";
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
  Tabs,
  Tab,
  Box,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
} from "@material-ui/core";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
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
  tabPanel: {
    padding: theme.spacing(2),
    minHeight: 400,
  },
  agentCard: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
  },
  uploadArea: {
    border: `2px dashed ${theme.palette.divider}`,
    borderRadius: theme.spacing(1),
    padding: theme.spacing(3),
    textAlign: "center",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: theme.palette.action.hover,
    },
  },
  knowledgeItem: {
    marginBottom: theme.spacing(1),
  },
}));

const TabPanel = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const availableTools = [
  { id: "google_sheets", name: "Google Sheets", description: "Ler e escrever em planilhas" },
  { id: "google_drive", name: "Google Drive", description: "Acessar arquivos do Drive" },
  { id: "knowledge_search", name: "Busca em Conhecimento", description: "Buscar na base de conhecimento" },
  { id: "web_search", name: "Busca Web", description: "Pesquisar informações na web" },
  { id: "calculator", name: "Calculadora", description: "Realizar cálculos" },
];

const personalities = [
  { value: "professional", label: "Profissional" },
  { value: "friendly", label: "Amigável" },
  { value: "empathetic", label: "Empático" },
  { value: "technical", label: "Técnico" },
  { value: "sales", label: "Vendedor" },
];

const CrewEditorModal = ({ open, onClose, crewId }) => {
  const classes = useStyles();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [blueprint, setBlueprint] = useState(null);
  const [crew, setCrew] = useState(null);

  // Estado dos agentes
  const [agents, setAgents] = useState([]);
  const [editingAgent, setEditingAgent] = useState(null);
  const [agentForm, setAgentForm] = useState({
    name: "",
    role: "",
    goal: "",
    backstory: "",
    personality: "professional",
  });

  // Estado das tools
  const [selectedTools, setSelectedTools] = useState([]);

  // Estado dos guardrails
  const [guardrails, setGuardrails] = useState([]);
  const [guardrailText, setGuardrailText] = useState("");

  // Estado do knowledge base
  const [knowledgeFiles, setKnowledgeFiles] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    if (open && crewId) {
      fetchCrewData();
    } else if (!open) {
      resetForm();
    }
  }, [open, crewId]);

  const fetchCrewData = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/crews/${crewId}`);
      setCrew(data.crew);

      if (data.blueprint) {
        setBlueprint(data.blueprint);
        setAgents(data.blueprint.agents || []);
        setSelectedTools(data.blueprint.tools || []);
        setGuardrails(data.blueprint.guardrails || []);
        setKnowledgeFiles(data.blueprint.knowledge_files || []);
      }
    } catch (err) {
      toastError(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTabValue(0);
    setBlueprint(null);
    setCrew(null);
    setAgents([]);
    setEditingAgent(null);
    setAgentForm({
      name: "",
      role: "",
      goal: "",
      backstory: "",
      personality: "professional",
    });
    setSelectedTools([]);
    setGuardrails([]);
    setGuardrailText("");
    setKnowledgeFiles([]);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // ===== AGENTES =====
  const handleAddAgent = () => {
    if (!agentForm.name || !agentForm.role || !agentForm.goal) {
      toast.error("Preencha nome, role e goal do agente");
      return;
    }

    if (editingAgent !== null) {
      const updated = [...agents];
      updated[editingAgent] = { ...agentForm };
      setAgents(updated);
      setEditingAgent(null);
    } else {
      setAgents([...agents, { ...agentForm }]);
    }

    setAgentForm({
      name: "",
      role: "",
      goal: "",
      backstory: "",
      personality: "professional",
    });
  };

  const handleEditAgent = (index) => {
    setAgentForm(agents[index]);
    setEditingAgent(index);
  };

  const handleDeleteAgent = (index) => {
    const updated = agents.filter((_, i) => i !== index);
    setAgents(updated);
    if (editingAgent === index) {
      setEditingAgent(null);
      setAgentForm({
        name: "",
        role: "",
        goal: "",
        backstory: "",
        personality: "professional",
      });
    }
  };

  // ===== TOOLS =====
  const handleToggleTool = (toolId) => {
    if (selectedTools.includes(toolId)) {
      setSelectedTools(selectedTools.filter(id => id !== toolId));
    } else {
      setSelectedTools([...selectedTools, toolId]);
    }
  };

  // ===== GUARDRAILS =====
  const handleAddGuardrail = () => {
    if (!guardrailText.trim()) return;
    setGuardrails([...guardrails, guardrailText.trim()]);
    setGuardrailText("");
  };

  const handleDeleteGuardrail = (index) => {
    setGuardrails(guardrails.filter((_, i) => i !== index));
  };

  // ===== KNOWLEDGE BASE =====
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingFile(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Chama backend que repassa para o CrewAI Service
      const { data } = await api.post(`/crews/${crewId}/knowledge/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setKnowledgeFiles([...knowledgeFiles, data]);
      toast.success(`Arquivo "${file.name}" enviado com sucesso!`);
    } catch (err) {
      toastError(err);
    } finally {
      setUploadingFile(false);
      event.target.value = null; // Reset input
    }
  };

  const handleDeleteKnowledge = async (fileId) => {
    try {
      await api.delete(`/crews/${crewId}/knowledge/${fileId}`);
      setKnowledgeFiles(knowledgeFiles.filter(f => f.id !== fileId));
      toast.success("Arquivo removido!");
    } catch (err) {
      toastError(err);
    }
  };

  // ===== SALVAR =====
  const handleSave = async () => {
    if (agents.length === 0) {
      toast.error("Adicione pelo menos um agente");
      return;
    }

    setSaving(true);
    try {
      const updatedBlueprint = {
        ...blueprint,
        agents,
        tools: selectedTools,
        guardrails,
        knowledge_files: knowledgeFiles,
      };

      await api.put(`/crews/${crewId}`, {
        blueprint: updatedBlueprint,
      });

      toast.success("Equipe atualizada com sucesso!");
      handleClose();
    } catch (err) {
      toastError(err);
    } finally {
      setSaving(false);
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
        Editor de Equipe {crew?.name && `- ${crew.name}`}
      </DialogTitle>

      <Tabs
        value={tabValue}
        onChange={handleTabChange}
        indicatorColor="primary"
        textColor="primary"
        variant="fullWidth"
      >
        <Tab label="Agentes" />
        <Tab label="Ferramentas" />
        <Tab label="Guardrails" />
        <Tab label="Base de Conhecimento" />
      </Tabs>

      <DialogContent dividers style={{ minHeight: 500 }}>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" height={400}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* TAB 0: AGENTES */}
            <TabPanel value={tabValue} index={0}>
              <Box className={classes.tabPanel}>
                <Typography variant="h6" gutterBottom>
                  Configurar Agentes
                </Typography>

                <Paper className={classes.agentCard} elevation={0}>
                  <TextField
                    label="Nome do Agente"
                    fullWidth
                    margin="dense"
                    value={agentForm.name}
                    onChange={(e) => setAgentForm({...agentForm, name: e.target.value})}
                  />
                  <TextField
                    label="Role (Função)"
                    fullWidth
                    margin="dense"
                    value={agentForm.role}
                    onChange={(e) => setAgentForm({...agentForm, role: e.target.value})}
                    placeholder="Ex: Atendente de Vendas, Suporte Técnico"
                  />
                  <TextField
                    label="Goal (Objetivo)"
                    fullWidth
                    margin="dense"
                    multiline
                    rows={2}
                    value={agentForm.goal}
                    onChange={(e) => setAgentForm({...agentForm, goal: e.target.value})}
                    placeholder="Ex: Ajudar clientes com dúvidas sobre produtos"
                  />
                  <TextField
                    label="Backstory (História)"
                    fullWidth
                    margin="dense"
                    multiline
                    rows={3}
                    value={agentForm.backstory}
                    onChange={(e) => setAgentForm({...agentForm, backstory: e.target.value})}
                    placeholder="Ex: Você é um especialista em produtos..."
                  />
                  <FormControl fullWidth margin="dense">
                    <InputLabel>Personalidade</InputLabel>
                    <Select
                      value={agentForm.personality}
                      onChange={(e) => setAgentForm({...agentForm, personality: e.target.value})}
                    >
                      {personalities.map(p => (
                        <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Box mt={2}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<AddIcon />}
                      onClick={handleAddAgent}
                    >
                      {editingAgent !== null ? "Atualizar Agente" : "Adicionar Agente"}
                    </Button>
                  </Box>
                </Paper>

                <Box mt={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Agentes Configurados ({agents.length})
                  </Typography>
                  <List>
                    {agents.map((agent, index) => (
                      <Paper key={index} style={{ marginBottom: 8, padding: 8 }}>
                        <ListItem>
                          <ListItemText
                            primary={agent.name}
                            secondary={`${agent.role} - ${agent.personality}`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton edge="end" onClick={() => handleEditAgent(index)}>
                              <AddIcon />
                            </IconButton>
                            <IconButton edge="end" onClick={() => handleDeleteAgent(index)}>
                              <DeleteIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      </Paper>
                    ))}
                  </List>
                </Box>
              </Box>
            </TabPanel>

            {/* TAB 1: FERRAMENTAS */}
            <TabPanel value={tabValue} index={1}>
              <Box className={classes.tabPanel}>
                <Typography variant="h6" gutterBottom>
                  Ferramentas Disponíveis
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Selecione as ferramentas que os agentes podem usar
                </Typography>

                <List>
                  {availableTools.map((tool) => (
                    <Paper key={tool.id} style={{ marginBottom: 8, padding: 8 }}>
                      <ListItem>
                        <ListItemText
                          primary={tool.name}
                          secondary={tool.description}
                        />
                        <ListItemSecondaryAction>
                          <Switch
                            edge="end"
                            checked={selectedTools.includes(tool.id)}
                            onChange={() => handleToggleTool(tool.id)}
                          />
                        </ListItemSecondaryAction>
                      </ListItem>
                    </Paper>
                  ))}
                </List>
              </Box>
            </TabPanel>

            {/* TAB 2: GUARDRAILS */}
            <TabPanel value={tabValue} index={2}>
              <Box className={classes.tabPanel}>
                <Typography variant="h6" gutterBottom>
                  Regras de Segurança (Guardrails)
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Defina limites e regras que os agentes devem seguir
                </Typography>

                <Box display="flex" gap={1} mb={2}>
                  <TextField
                    fullWidth
                    label="Nova regra"
                    value={guardrailText}
                    onChange={(e) => setGuardrailText(e.target.value)}
                    placeholder="Ex: Nunca fornecer informações de preço sem confirmar estoque"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleAddGuardrail();
                      }
                    }}
                  />
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleAddGuardrail}
                  >
                    <AddIcon />
                  </Button>
                </Box>

                <List>
                  {guardrails.map((rule, index) => (
                    <Paper key={index} className={classes.knowledgeItem}>
                      <ListItem>
                        <ListItemText primary={rule} />
                        <ListItemSecondaryAction>
                          <IconButton edge="end" onClick={() => handleDeleteGuardrail(index)}>
                            <DeleteIcon />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    </Paper>
                  ))}
                </List>
              </Box>
            </TabPanel>

            {/* TAB 3: KNOWLEDGE BASE */}
            <TabPanel value={tabValue} index={3}>
              <Box className={classes.tabPanel}>
                <Typography variant="h6" gutterBottom>
                  Base de Conhecimento
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Faça upload de documentos para a equipe consultar
                </Typography>

                <input
                  accept=".pdf,.txt,.doc,.docx"
                  style={{ display: 'none' }}
                  id="knowledge-upload"
                  type="file"
                  onChange={handleFileUpload}
                />
                <label htmlFor="knowledge-upload">
                  <Paper className={classes.uploadArea} elevation={0}>
                    <CloudUploadIcon style={{ fontSize: 48, color: '#666' }} />
                    <Typography variant="body1" gutterBottom>
                      {uploadingFile ? "Enviando..." : "Clique para fazer upload"}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Formatos: PDF, TXT, DOC, DOCX
                    </Typography>
                  </Paper>
                </label>

                <Box mt={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Arquivos ({knowledgeFiles.length})
                  </Typography>
                  <List>
                    {knowledgeFiles.map((file) => (
                      <Paper key={file.id} className={classes.knowledgeItem}>
                        <ListItem>
                          <DescriptionIcon style={{ marginRight: 16 }} />
                          <ListItemText
                            primary={file.name}
                            secondary={`${(file.size / 1024).toFixed(2)} KB`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton edge="end" onClick={() => handleDeleteKnowledge(file.id)}>
                              <DeleteIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      </Paper>
                    ))}
                  </List>
                </Box>
              </Box>
            </TabPanel>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} color="secondary" variant="outlined">
          Cancelar
        </Button>
        <div className={classes.btnWrapper}>
          <Button
            onClick={handleSave}
            color="primary"
            variant="contained"
            disabled={saving || loading}
          >
            Salvar Equipe
          </Button>
          {saving && (
            <CircularProgress size={24} className={classes.buttonProgress} />
          )}
        </div>
      </DialogActions>
    </Dialog>
  );
};

export default CrewEditorModal;
