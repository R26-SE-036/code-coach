package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug020 {
    public void checkConnection(int retries) {
        boolean failed = false;
        if (failed = retries > 3) {
            System.out.println("Connection failed");
        }
    }
}
