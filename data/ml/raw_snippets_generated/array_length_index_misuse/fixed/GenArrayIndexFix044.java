public class GenArrayIndexFix044 {
    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }

    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
