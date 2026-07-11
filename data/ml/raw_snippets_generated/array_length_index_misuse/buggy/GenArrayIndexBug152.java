public class GenArrayIndexBug152 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void stampLast(int[] ages, int value) {
        ages[ages.length] = value;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }
}
