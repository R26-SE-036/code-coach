package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug011 {
    public void checkStatus(int status) {
        boolean running = false;
        while (running = status != 0) {
            System.out.println("Processing...");
            status--;
        }
    }
}
