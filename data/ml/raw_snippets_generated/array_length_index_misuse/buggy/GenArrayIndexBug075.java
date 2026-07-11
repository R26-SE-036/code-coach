public class GenArrayIndexBug075 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void showLast(int[] totals) {
        System.out.println(totals[totals.length]);
    }
}
