package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix020 {
    public void checkConnection(int retries) {
        boolean failed = retries > 3;
        if (failed) {
            System.out.println("Connection failed");
        }
    }
}
