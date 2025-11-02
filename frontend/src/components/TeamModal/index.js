import React, { useState, useEffect } from "react";
import * as Yup from "yup";
import { Formik, Form, Field } from "formik";
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
  InputLabel,
  MenuItem,
  Select,
  FormControlLabel,
  Switch,
} from "@material-ui/core";

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
}));

const TeamSchema = Yup.object().shape({
  name: Yup.string()
    .min(2, "Nome muito curto")
    .max(100, "Nome muito longo")
    .required("Nome é obrigatório"),
  industry: Yup.string().required("Indústria é obrigatória"),
});

const TeamModal = ({ open, onClose, teamId }) => {
  const classes = useStyles();

  const initialState = {
    name: "",
    description: "",
    industry: "other",
    isActive: true,
  };

  const [team, setTeam] = useState(initialState);

  useEffect(() => {
    const fetchTeam = async () => {
      if (!teamId) return;
      try {
        const { data } = await api.get(`/teams/${teamId}`);
        setTeam({
          name: data.team.name,
          description: data.team.description || "",
          industry: data.team.industry || "other",
          isActive: data.team.isActive,
        });
      } catch (err) {
        toastError(err);
      }
    };
    fetchTeam();
  }, [teamId, open]);

  const handleClose = () => {
    setTeam(initialState);
    onClose();
  };

  const handleSaveTeam = async (values) => {
    try {
      const payload = {
        ...values,
        generatedBy: "manual",
      };

      if (teamId) {
        await api.put(`/teams/${teamId}`, payload);
        toast.success("Equipe atualizada com sucesso!");
      } else {
        await api.post("/teams", payload);
        toast.success("Equipe criada com sucesso!");
      }
      handleClose();
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <div className={classes.root}>
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth scroll="paper">
        <DialogTitle>
          {teamId ? "Editar Equipe" : "Criar Equipe"}
        </DialogTitle>
        <Formik
          initialValues={team}
          enableReinitialize={true}
          validationSchema={TeamSchema}
          onSubmit={(values, actions) => {
            setTimeout(() => {
              handleSaveTeam(values);
              actions.setSubmitting(false);
            }, 400);
          }}
        >
          {({ touched, errors, isSubmitting, values, setFieldValue }) => (
            <Form>
              <DialogContent dividers>
                <div className={classes.textField}>
                  <Field
                    as={TextField}
                    label="Nome da Equipe"
                    name="name"
                    error={touched.name && Boolean(errors.name)}
                    helperText={touched.name && errors.name}
                    variant="outlined"
                    margin="dense"
                    fullWidth
                  />
                </div>

                <div className={classes.textField}>
                  <Field
                    as={TextField}
                    label="Descrição"
                    name="description"
                    multiline
                    rows={3}
                    variant="outlined"
                    margin="dense"
                    fullWidth
                  />
                </div>

                <div className={classes.textField}>
                  <FormControl variant="outlined" margin="dense" fullWidth>
                    <InputLabel>Indústria</InputLabel>
                    <Field
                      as={Select}
                      label="Indústria"
                      name="industry"
                      error={touched.industry && Boolean(errors.industry)}
                    >
                      <MenuItem value="ecommerce">E-commerce</MenuItem>
                      <MenuItem value="services">Serviços</MenuItem>
                      <MenuItem value="technology">Tecnologia</MenuItem>
                      <MenuItem value="health">Saúde</MenuItem>
                      <MenuItem value="education">Educação</MenuItem>
                      <MenuItem value="finance">Finanças</MenuItem>
                      <MenuItem value="retail">Varejo</MenuItem>
                      <MenuItem value="real_estate">Imobiliário</MenuItem>
                      <MenuItem value="other">Outro</MenuItem>
                    </Field>
                  </FormControl>
                </div>

                <div className={classes.textField}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={values.isActive}
                        onChange={(e) => setFieldValue("isActive", e.target.checked)}
                        name="isActive"
                        color="primary"
                      />
                    }
                    label="Equipe Ativa"
                  />
                </div>
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
                    {teamId ? "Salvar" : "Criar"}
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

export default TeamModal;
