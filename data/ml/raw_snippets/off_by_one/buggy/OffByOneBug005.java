package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug005 {
    public static void main(String[] args) {
        char[] word = { 'J', 'A', 'V', 'A' };

        for (int i = 0; i <= word.length; i++) {
            System.out.println(word[i]);
        }
    }
}