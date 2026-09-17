package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug025 {
    public static void main(String[] args) {
        char letter = 'a';
        while (letter <= 'e') {
            System.out.print(letter + " ");
        }
        System.out.println();
    }
}
