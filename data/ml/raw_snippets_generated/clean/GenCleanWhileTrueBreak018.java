public class GenCleanWhileTrueBreak018 {
    static int spin(int quota) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > quota) {
                break;
            }
        }
        return rounds;
    }
}
