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
} from "@material-ui/core";
import { Add, Delete } from "@material-ui/icons";

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
  };

  const [agent, setAgent] = useState(initialState);

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
        });
      } catch (err) {
        toastError(err);
      }
    };
    fetchAgent();
  }, [agentId, teamId, open]);

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
