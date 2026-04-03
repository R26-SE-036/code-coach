package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix023 {
    public void checkPrime(int n) {
        boolean prime = true;
        for (int i = 2; i < n; i++) {
            if (n % i == 0) {
                prime = false;
                System.out.println("Not prime");
                break;
            }
        }
    }
}
