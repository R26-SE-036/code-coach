public class GenArrayIndexBug074 {
    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static void printAll5(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static void stampLast(int[] weights, int value) {
        weights[weights.length] = value;
    }
}
