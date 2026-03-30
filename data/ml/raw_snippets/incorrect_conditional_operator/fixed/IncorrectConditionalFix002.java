package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix002 {
    public static void main(String[] args) {
        boolean active = false;

        if (active == true) {
            System.out.println("Active");
        }
    }
}