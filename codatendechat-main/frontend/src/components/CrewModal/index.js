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
} from "@material-ui/core";
import { Add as AddIcon, Delete as DeleteIcon } from "@material-ui/icons";

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
}));

const AgentSchema = Yup.object().shape({
  name: Yup.string().required("Nome é obrigatório"),
  role: Yup.string().required("Função é obrigatória"),
  goal: Yup.string().required("Objetivo é obrigatório"),
  backstory: Yup.string().required("História é obrigatória"),
  useKnowledge: Yup.boolean(),
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
            },
          ],
        });
        return;
      }

      setLoading(true);
      try {
        const { data } = await api.get(`/crews/${crewId}`);

        // Converter agents de objeto para array
        const agentsArray = data.agents
          ? Object.values(data.agents).map(agent => ({
              name: agent.name || "",
              role: agent.role || "",
              goal: agent.goal || "",
              backstory: agent.backstory || "",
              useKnowledge: agent.knowledgeDocuments?.length > 0 || false,
            }))
          : [{
              name: "",
              role: "",
              goal: "",
              backstory: "",
              useKnowledge: false,
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
          keywords: [],
          personality: {
            tone: "professional",
            traits: [],
            customInstructions: "",
          },
          tools: [],
          toolConfigs: {},
          knowledgeDocuments: agent.useKnowledge ? [] : [],
          training: {
            guardrails: {
              do: [],
              dont: [],
            },
            persona: agent.backstory,
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
                        <Box key={index} className={classes.agentCard}>
                          {values.agents.length > 1 && (
                            <IconButton
                              size="small"
                              className={classes.deleteButton}
                              onClick={() => remove(index)}
                              color="secondary"
                            >
                              <DeleteIcon />
                            </IconButton>
                          )}

                          <Typography variant="subtitle2" gutterBottom>
                            Agente {index + 1}
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
                            label="Função"
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
                            label="Objetivo"
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
                            label="História"
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
                            rows={2}
                            size="small"
                          />

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
                                label="Usar base de conhecimento"
                              />
                            )}
                          </Field>
                        </Box>
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
                          })
                        }
                        fullWidth
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
