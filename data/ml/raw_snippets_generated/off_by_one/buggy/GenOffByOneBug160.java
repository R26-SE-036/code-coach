public class GenOffByOneBug160 {
    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i <= values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }

    static int drain1(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
