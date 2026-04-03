public class Clean019 {
    public String joinWords(String[] words, String separator) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < words.length; i++) {
            sb.append(words[i]);
            if (i < words.length - 1) {
                sb.append(separator);
            }
        }
        return sb.toString();
    }
}
