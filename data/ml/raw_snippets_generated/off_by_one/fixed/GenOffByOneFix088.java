public class GenOffByOneFix088 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static int drain3(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static void printAll4(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }
}
