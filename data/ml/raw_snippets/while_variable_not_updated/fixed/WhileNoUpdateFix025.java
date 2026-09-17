package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix025 {
    public static void main(String[] args) {
        char letter = 'a';
        while (letter <= 'e') {
            System.out.print(letter + " ");
            letter++;
        }
        System.out.println();
    }
}
