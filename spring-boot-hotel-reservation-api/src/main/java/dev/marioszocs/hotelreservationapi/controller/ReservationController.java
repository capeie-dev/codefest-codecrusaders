package dev.marioszocs.hotelreservationapi.controller;

import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.service.ReservationService;
import dev.marioszocs.hotelreservationapi.validator.ReservationValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Reservation Controller containing endpoints for Reservation-related API calls.
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/api/v1")
public class ReservationController {

    private final ReservationService reservationService;

    /**
     * Retrieves the list of all reservations.
     *
     * @return a list of {@link Reservation} objects
     */
    @GetMapping(value = "/reservations", produces = "application/json")
    public List<Reservation> getReservationList() {
        log.info("Fetching all reservations");
        return reservationService.getAllReservations();
    }

    /**
     * Retrieves a specific reservation by its ID.
     *
     * @param reservationId the ID of the reservation to retrieve
     * @return the {@link Reservation} object
     */
    @GetMapping(value = "/reservation/{id}", produces = "application/json")
    public Reservation getReservation(@PathVariable("id") Integer reservationId) {
        ReservationValidator.validateId(reservationId);
        log.info("Fetching reservation with ID: {}", reservationId);
        return reservationService.getReservation(reservationId);
    }

    /**
     * Saves a new reservation or updates an existing one.
     *
     * @param reservation the {@link Reservation} object to save
     * @return an {@link IdEntity} containing the ID of the saved reservation
     */
    @PostMapping(value = "/reservation", produces = "application/json")
    public IdEntity saveReservation(@RequestBody Reservation reservation) {
        ReservationValidator.validateReservationPOST(reservation);
        log.info("Saving reservation: {}", reservation);
        return reservationService.saveReservation(reservation);
    }

    /**
     * Deletes the reservation identified by the given ID.
     *
     * @param reservationId the ID of the reservation to delete
     * @return a {@link SuccessEntity} indicating the result of the deletion
     */
    @DeleteMapping(value = "/reservation/{id}", produces = "application/json")
    public SuccessEntity deleteReservation(@PathVariable("id") Integer reservationId) {
        ReservationValidator.validateId(reservationId);
        log.info("Deleting reservation with ID: {}", reservationId);
        return reservationService.deleteReservation(reservationId);
    }
}
