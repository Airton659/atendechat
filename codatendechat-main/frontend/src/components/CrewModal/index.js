import React, { useState, useEffect } from "react";
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
  FormControlLabel,
  Switch,
} from "@material-ui/core";

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
}));

const CrewSchema = Yup.object().shape({
  name: Yup.string()
    .min(2, "Nome muito curto")
    .max(100, "Nome muito longo")
    .required("Nome é obrigatório"),
  description: Yup.string()
    .max(500, "Descrição muito longa"),
});

const CrewModal = ({ open, onClose, crewId }) => {
  const classes = useStyles();
  const [crew, setCrew] = useState({
    name: "",
    description: "",
    isActive: true,
  });

  useEffect(() => {
    const fetchCrew = async () => {
      if (!crewId) return;
      try {
        const { data } = await api.get(`/crews/${crewId}`);
        setCrew(data.crew);
      } catch (err) {
        toastError(err);
      }
    };
    fetchCrew();
  }, [crewId, open]);

  const handleClose = () => {
    setCrew({
      name: "",
      description: "",
      isActive: true,
    });
    onClose();
  };

  const handleSaveCrew = async (values) => {
    try {
      if (crewId) {
        await api.put(`/crews/${crewId}`, values);
        toast.success(i18n.t("crews.toasts.updated"));
      } else {
        await api.post("/crews", values);
        toast.success(i18n.t("crews.toasts.created"));
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
      maxWidth="sm"
      fullWidth
      scroll="paper"
    >
      <DialogTitle id="form-dialog-title">
        {crewId
          ? i18n.t("crews.dialog.edit")
          : i18n.t("crews.dialog.add")}
      </DialogTitle>
      <Formik
        initialValues={crew}
        enableReinitialize={true}
        validationSchema={CrewSchema}
        onSubmit={(values, actions) => {
          setTimeout(() => {
            handleSaveCrew(values);
            actions.setSubmitting(false);
          }, 400);
        }}
      >
        {({ touched, errors, isSubmitting, values, setFieldValue }) => (
          <Form>
            <DialogContent dividers>
              <div className={classes.root}>
                <Field
                  as={TextField}
                  label={i18n.t("crews.form.name")}
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
                  label={i18n.t("crews.form.description")}
                  name="description"
                  error={touched.description && Boolean(errors.description)}
                  helperText={touched.description && errors.description}
                  variant="outlined"
                  margin="dense"
                  multiline
                  rows={4}
                  fullWidth
                  className={classes.textField}
                />
              </div>
              <div className={classes.root}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={values.isActive}
                      onChange={(e) => setFieldValue("isActive", e.target.checked)}
                      name="isActive"
                      color="primary"
                    />
                  }
                  label={i18n.t("crews.form.isActive")}
                />
              </div>
            </DialogContent>
            <DialogActions>
              <Button
                onClick={handleClose}
                color="secondary"
                disabled={isSubmitting}
                variant="outlined"
              >
                {i18n.t("crews.buttons.cancel")}
              </Button>
              <div className={classes.btnWrapper}>
                <Button
                  type="submit"
                  color="primary"
                  disabled={isSubmitting}
                  variant="contained"
                  className={classes.btnWrapper}
                >
                  {crewId
                    ? i18n.t("crews.buttons.okEdit")
                    : i18n.t("crews.buttons.okAdd")}
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
    </Dialog>
  );
};

export default CrewModal;
