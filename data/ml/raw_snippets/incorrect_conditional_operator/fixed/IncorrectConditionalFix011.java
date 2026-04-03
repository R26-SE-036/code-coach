package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix011 {
    public void checkStatus(int status) {
        boolean running = status != 0;
        while (running) {
            System.out.println("Processing...");
            status--;
            running = status != 0;
        }
    }
}
