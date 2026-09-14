package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix006 {
    public static void main(String[] args) {
        String word = "education";
        int vowels = 0;
        int others = 0;
        for (int i = 0; i < word.length(); i++) {
            switch (word.charAt(i)) {
                case 'a':
                case 'e':
                case 'i':
                case 'o':
                case 'u':
                    vowels++;
                    break;
                default:
                    others++;
            }
        }
        System.out.println(vowels + " vowels, " + others + " others");
    }
}
