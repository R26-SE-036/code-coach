package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix011 {
    static int paymentsNeeded(double balance, double payment) {
        int payments = 0;
        while (balance > 0) {
            payments = payments + 1;
            balance = balance - payment;
        }
        return payments;
    }
}
