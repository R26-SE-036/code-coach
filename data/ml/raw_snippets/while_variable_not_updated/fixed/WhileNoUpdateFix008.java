package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix008 {
    public static void main(String[] args) {
        int secret = 7;
        int guess = 3;
        int attempts = 0;
        while (guess != secret) {
            attempts++;
            guess++;
            System.out.println("Wrong guess: " + guess);
        }
        System.out.println("Found after " + attempts + " attempts");
    }
}
