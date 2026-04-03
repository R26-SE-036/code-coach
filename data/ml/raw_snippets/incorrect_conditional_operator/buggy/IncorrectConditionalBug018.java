package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug018 {
    public void checkPermission(String user) {
        boolean allowed = false;
        if (allowed = user.equals("root")) {
            System.out.println("Root access granted");
        }
    }
}
