***** Code to implement the pull-to-center decision rule *****

* Make sure to replace `path_to_csv_file` with the appropriate path to the csv file with the
* raw data (raw_data_r1_Stata.csv)
import delimited path_to_csv_file

* Generate a categorical variable from an existing string variable. In this case, we generate
* a categorical variable that captures the experiment. This variable is later used to filter
* the appropriate data for the estimation
encode experiment, gen(experiment_encoded)

* This is the program that defines the decision rule
global panel = "subject_id_r"
capture program drop RE_ANCHORING
program RE_ANCHORING
args todo b lnfj
tempvar anchor q_opt z z2 T a S_z2 S_temp Sz_2 first
tempname sigma_u sigma_e ln_sigma_u ln_sigma_e
mleval `anchor' = `b', eq(1)
mleval `ln_sigma_u' = `b', eq(2) scalar
mleval `ln_sigma_e' = `b', eq(3) scalar 
scalar `sigma_u' = exp(`ln_sigma_u')
scalar `sigma_e' = exp(`ln_sigma_e')
sort $panel
qui {
generate double `q_opt' = $ML_y2
generate double `z' = `anchor'*50 + (1 - `anchor')*`q_opt'
generate double `z2' = $ML_y1 - `z'
by $panel: generate `T' = _N
generate double `a' = `sigma_u'^2 / ( `T' * `sigma_u'^2 + `sigma_e'^2 )
by $panel: egen double `S_z2' = sum( `z2'^2 )
by $panel: egen double `S_temp' = sum( `z2' )
by $panel: generate double `Sz_2' = `S_temp'^2
by $panel: generate `first' = ( _n == 1 )
mlsum `lnfj' = -.5 * ( ( `S_z2' - `a' * `Sz_2' ) / ( `sigma_e'^2 ) + log( `T' * `sigma_u'^2 / `sigma_e'^2 + 1 ) + `T' * log( 2*_pi * `sigma_e'^2 ) ) if `first' == 1
}  
end

* Maximum-likelihood (ML) estimation for the Main Experiment
ml model d0 RE_ANCHORING ( anchor: order optimum = ) ( ln_sigma_u: ) ( ln_sigma_e: ) if experiment_encoded == 2 & included_treatment == 1, technique(nr)  
ml check
ml maximize, difficult

* ML estimation for the Salience Experiment
ml model d0 RE_ANCHORING ( anchor: order optimum = ) ( ln_sigma_u: ) ( ln_sigma_e: ) if experiment_encoded == 3, technique(nr)  
ml check
ml maximize, difficult


***** Code to estimate the marginal effects *****

* Set the indexes to run a random-effects (RE) model  
xtset subject_id_r round

* Generate categorical variables from existing string variables. In this case, we generate a
* categorical variable that captures the experiment. This variable is later used to filter the
* appropriate data for the estimation (this is done above in line 10). We also generate a
* categorical variable that captures a piece of demographic information
encode related_course_r, gen(related_course_r_encoded)

* RE estimation
xtreg order c.expediting_cost##ib2.experiment_encoded lagdemand lagshortage lagleftover round i.gender_r age semester i.related_course_r_encoded if ((experiment_encoded == 2 & included_treatment == 1) | experiment_encoded == 3), re

* Marginal effects estimation. We include a plot to see the results graphically
margins ib2.experiment_encoded, at(expediting_cost = (4 6 12 18 30))
marginsplot


***** Code to estimate the additional models for the Main Experiment *****

* Set the indexes to run a random-effects (RE) model (this is done above in line 53)

* Generate categorical variables from existing string variables. In this case, we generate a
* categorical variable that captures the experiment. This variable is later used to filter the
* appropriate data for the estimation (this is done above in line 10). We also generate a dummy
* variable that captures a piece of demographic information. By dummifying the variable, Stata
* shows all the estimation output, which doesn't happen if we input the variable as categorical
tab related_course_r, gen(r_c)

* RE estimation with robust SE
xtreg order expediting_cost lagdemand lagshortage lagleftover round gender_r age semester r_c2 if experiment_encoded == 2 & included_treatment == 1, re vce(r)

* GLS estimation with AR1 autocorrelation
xtgls order expediting_cost lagdemand lagshortage lagleftover round gender_r semester r_c2 if experiment_encoded == 2 & included_treatment == 1, corr(ar1)

* GLS estimation with panel-specific AR1 autocorrelation
xtgls order expediting_cost lagdemand lagshortage lagleftover round gender_r age semester r_c2 if experiment_encoded == 2 & included_treatment == 1, corr(psar1)
