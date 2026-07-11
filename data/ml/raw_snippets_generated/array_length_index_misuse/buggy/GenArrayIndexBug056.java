public class GenArrayIndexBug056 {
    static void printAll1(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven4(int count) {
        return count % 2 == 0;
    }

    static void showLast(int[] stocks) {
        System.out.println(stocks[stocks.length]);
    }

    static int drain5(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static boolean isEven6(int stock) {
        return stock % 2 == 0;
    }

    static String join7(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
