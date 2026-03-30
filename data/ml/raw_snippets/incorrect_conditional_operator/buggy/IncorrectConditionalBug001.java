package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug001 {
    public static void main(String[] args) {
        boolean isAdmin = false;
        String role = "ADMIN";

        if (isAdmin = role.equals("ADMIN")) {
            System.out.println("Access granted");
        }
    }
}