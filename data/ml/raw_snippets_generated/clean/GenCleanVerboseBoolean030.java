public class GenCleanVerboseBoolean030 {
    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static String toggle(boolean valid) {
        if (valid == true) {
            return "on";
        }
        return "off";
    }
}
