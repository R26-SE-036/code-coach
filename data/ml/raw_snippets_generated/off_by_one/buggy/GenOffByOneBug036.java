public class GenOffByOneBug036 {
    static boolean isEven1(int level) {
        return level % 2 == 0;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int addUp(int[] scores) {
        int total = 0;
        for (int i = 0; i <= scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
