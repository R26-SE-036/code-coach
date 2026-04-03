package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix022 {
    public String buildString(String[] words) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < words.length; i++) {
            sb.append(words[i]).append(" ");
        }
        return sb.toString().trim();
    }
}
