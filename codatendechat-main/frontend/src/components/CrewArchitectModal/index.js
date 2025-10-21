import React, { useState } from "react";
import * as Yup from "yup";
import { Formik, Form, Field } from "formik";
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Divider,
} from "@material-ui/core";
import { Stars as AutoAwesomeIcon } from "@material-ui/icons";

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
  tabContent: {
    marginTop: theme.spacing(2),
    minHeight: 300,
  },
  agentItem: {
    marginBottom: theme.spacing(1),
    backgroundColor: theme.palette.background.default,
    borderRadius: 4,
  },
}));

const ArchitectSchema = Yup.object().shape({
  businessDescription: Yup.string()
    .min(20, "Descrição muito curta (mínimo 20 caracteres)")
    .max(1000, "Descrição muito longa (máximo 1000 caracteres)")
    .required("Descrição do negócio é obrigatória"),
  industry: Yup.string()
    .required("Indústria é obrigatória"),
});

const industries = [
  { value: "ecommerce", label: "E-commerce" },
  { value: "services", label: "Serviços" },
  { value: "technology", label: "Tecnologia" },
  { value: "health", label: "Saúde" },
  { value: "education", label: "Educação" },
  { value: "finance", label: "Finanças" },
  { value: "retail", label: "Varejo" },
  { value: "real_estate", label: "Imobiliário" },
  { value: "other", label: "Outro" },
];

const CrewArchitectModal = ({ open, onClose, onSave }) => {
  const classes = useStyles();
  const [step, setStep] = useState(1);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generatedCrew, setGeneratedCrew] = useState(null);
  const [currentTab, setCurrentTab] = useState(0);

  const initialValues = {
    businessDescription: "",
    industry: "",
  };

  const handleClose = () => {
    setStep(1);
    setGeneratedCrew(null);
    setCurrentTab(0);
    onClose();
  };

  const handleGenerate = async (values) => {
    setGenerating(true);
    try {
      const { data } = await api.post("/crews/generate", values);
      setGeneratedCrew(data);
      setStep(2);
      toast.success("Equipe gerada com sucesso!");
    } catch (err) {
      toastError(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // A equipe já foi salva no Firestore pelo backend durante generate
      toast.success("Equipe salva com sucesso!");
      if (onSave) {
        onSave();
      }
      handleClose();
    } catch (err) {
      toastError(err);
    } finally {
      setSaving(false);
    }
  };

  const renderAgentsTab = () => {
    if (!generatedCrew?.blueprint?.agents) {
      return (
        <Typography variant="body2" color="textSecondary">
          Nenhum agente gerado
        </Typography>
      );
    }

    const agents = Array.isArray(generatedCrew.blueprint.agents)
      ? generatedCrew.blueprint.agents
      : Object.values(generatedCrew.blueprint.agents);

    return (
      <List>
        {agents.map((agent, idx) => (
          <React.Fragment key={idx}>
            <ListItem className={classes.agentItem}>
              <ListItemText
                primary={
                  <Typography variant="subtitle1" style={{ fontWeight: 600 }}>
                    {agent.name}
                  </Typography>
                }
                secondary={
                  <>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Função:</strong> {agent.role}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Objetivo:</strong> {agent.goal}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>História:</strong> {agent.backstory}
                    </Typography>
                  </>
                }
              />
            </ListItem>
            {idx < agents.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    );
  };

  const renderToolsTab = () => {
    if (!generatedCrew?.blueprint?.customTools) {
      return (
        <Typography variant="body2" color="textSecondary">
          Nenhuma ferramenta personalizada configurada
        </Typography>
      );
    }

    return (
      <List>
        {generatedCrew.blueprint.customTools.map((tool, idx) => (
          <React.Fragment key={idx}>
            <ListItem className={classes.agentItem}>
              <ListItemText
                primary={
                  <Typography variant="subtitle1" style={{ fontWeight: 600 }}>
                    {tool.name || `Ferramenta ${idx + 1}`}
                  </Typography>
                }
                secondary={
                  <Typography variant="body2" color="textSecondary">
                    {tool.description || "Sem descrição"}
                  </Typography>
                }
              />
            </ListItem>
            {idx < generatedCrew.blueprint.customTools.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    );
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
        <Box display="flex" alignItems="center" gap={1}>
          <AutoAwesomeIcon />
          <span>Gerar Equipe com IA</span>
        </Box>
      </DialogTitle>

      {step === 1 && (
        <Formik
          initialValues={initialValues}
          validationSchema={ArchitectSchema}
          onSubmit={handleGenerate}
        >
          {({ touched, errors, isSubmitting }) => (
            <Form>
              <DialogContent dividers>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Descreva seu negócio e deixe a IA criar uma equipe especializada para você
                </Typography>

                <div className={classes.root} style={{ marginTop: 16 }}>
                  <FormControl
                    variant="outlined"
                    margin="dense"
                    fullWidth
                    error={touched.industry && Boolean(errors.industry)}
                  >
                    <InputLabel>Setor/Indústria</InputLabel>
                    <Field
                      as={Select}
                      name="industry"
                      label="Setor/Indústria"
                    >
                      {industries.map((ind) => (
                        <MenuItem key={ind.value} value={ind.value}>
                          {ind.label}
                        </MenuItem>
                      ))}
                    </Field>
                  </FormControl>
                </div>

                <div className={classes.root}>
                  <Field
                    as={TextField}
                    label="Descrição do Negócio"
                    name="businessDescription"
                    error={
                      touched.businessDescription &&
                      Boolean(errors.businessDescription)
                    }
                    helperText={
                      touched.businessDescription && errors.businessDescription
                    }
                    variant="outlined"
                    margin="dense"
                    multiline
                    rows={8}
                    fullWidth
                    className={classes.textField}
                    placeholder="Descreva seu negócio, produtos, serviços, público-alvo e principais objetivos..."
                  />
                </div>
              </DialogContent>
              <DialogActions>
                <Button
                  onClick={handleClose}
                  color="secondary"
                  disabled={generating}
                  variant="outlined"
                >
                  Cancelar
                </Button>
                <div className={classes.btnWrapper}>
                  <Button
                    type="submit"
                    color="primary"
                    disabled={generating}
                    variant="contained"
                    startIcon={<AutoAwesomeIcon />}
                  >
                    Gerar Equipe
                  </Button>
                  {generating && (
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

      {step === 2 && generatedCrew && (
        <>
          <DialogContent dividers>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Equipe gerada com sucesso! Revise os agentes e ferramentas antes de salvar.
            </Typography>

            <Box mt={2}>
              <Tabs
                value={currentTab}
                onChange={(e, newValue) => setCurrentTab(newValue)}
                indicatorColor="primary"
                textColor="primary"
              >
                <Tab label="Agentes" />
                <Tab label="Ferramentas" />
              </Tabs>

              <div className={classes.tabContent}>
                {currentTab === 0 && renderAgentsTab()}
                {currentTab === 1 && renderToolsTab()}
              </div>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={handleClose}
              color="secondary"
              disabled={saving}
              variant="outlined"
            >
              Cancelar
            </Button>
            <div className={classes.btnWrapper}>
              <Button
                onClick={handleSave}
                color="primary"
                disabled={saving}
                variant="contained"
              >
                Salvar Equipe
              </Button>
              {saving && (
                <CircularProgress
                  size={24}
                  className={classes.buttonProgress}
                />
              )}
            </div>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
};

export default CrewArchitectModal;
