package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug023 {
    public void checkPrime(int n) {
        boolean prime = false;
        for (int i = 2; i < n; i++) {
            if (prime = n % i == 0) {
                System.out.println("Not prime");
                break;
            }
        }
    }
}
